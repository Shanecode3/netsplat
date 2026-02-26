import taichi as ti
import pywifi
import time
import threading
import math
import mlflow
from collections import deque
import ollama
import json


ti.init(arch=ti.gpu)
res_x, res_y = 800, 600
pixels = ti.Vector.field(3, dtype=ti.f32, shape=(res_x, res_y))

current_rssi = -100.0
signal_history = deque(maxlen=20)
latest_diagnosis = "Initializing AI..."
is_running = True

def wifi_scanner_loop():
    global current_rssi
    wifi = pywifi.PyWiFi()

    if len(wifi.interfaces()) == 0:
        print("NO wifi interface found! Following data is fake simulated data!")
        return
    
    iface = wifi.interfaces()[0]
    print(f"Scanner started on: {iface.name}")

    while is_running:
        try:
            iface.scan()
            time.sleep(1.5)

            results = iface.scan_results()
            best_signal = -100

            for network in results:
                if network.signal > best_signal:
                    best_signal = network.signal
            
            current_rssi = best_signal
            signal_history.append(best_signal)
            print(f"New signal: {current_rssi} dBm")

        except Exception as e:
            print(f"Scanner error: {e}")
            time.sleep(1)

def ai_agent_loop():
    global latest_diagnosis
    
    # System Prompt (The Rules)
    system_prompt = """
    You are a Network Diagnostic AI.
    Analyze the RSSI history (dBm).
    - > -50: Excellent
    - -50 to -70: Good
    - < -70: Weak
    - Drop > 10dB: Interference
    
    Output ONLY a short sentence (max 10 words). Example: "Signal Stable." or "Sudden Drop Detected."
    """
    
    print("🧠 AI Agent Online. Waiting for data...")
    time.sleep(5)

    while is_running:
        if len(signal_history) > 5:
            try:
                data_str = str(list(signal_history))
                response = ollama.chat(model = "llama3", messages=[{'role': 'system', 'content': system_prompt},{'role': 'user', 'content': f"History: {data_str}"}])
                latest_diagnosis = response['message']['content']
                print(f"AI: {latest_diagnosis}")
            
            except Exception as e:
                print(f"AI Err: {e}")
        
        time.sleep(10)

@ti.kernel
def paint(signal_strength_norm: ti.f32):

    center_x = 0.5
    center_y = 0.5

    for i, j in pixels:
        u = i / res_x
        v = j / res_y

        dx = u - center_x
        dy = v - center_y
        dist = ti.sqrt(dx**2 + dy**2)

        orb_radius_modifier = 3.0 + (signal_strength_norm * 10.0)

        glow = ti.exp(-dist * (20.0 - orb_radius_modifier))

        red = 1.0 - signal_strength_norm
        green = signal_strength_norm
        blue = 0.1

        pixels[i,j] = ti.Vector([red, green, blue]) * glow


if __name__ == "__main__":
    # Start Threads
    threading.Thread(target=wifi_scanner_loop, daemon=True).start()
    threading.Thread(target=ai_agent_loop, daemon=True).start()
    
    gui = ti.GUI("Signal Splat: AI Powered", res=(res_x, res_y))
    
    while gui.running:
        # Math: Normalize -90dBm to -40dBm into 0.0 to 1.0
        clamped = max(-90.0, min(-40.0, float(current_rssi)))
        normalized = (clamped - -90.0) / 50.0
        
        paint(normalized)
        
        gui.set_image(pixels)
        
        # HUD: Signal Strength
        gui.text(f"RSSI: {current_rssi} dBm", pos=(0.05, 0.95), color=0xFFFFFF, font_size=24)
        
        # HUD: AI Diagnosis (The New Part)
        gui.text(f"AI: {latest_diagnosis}", pos=(0.05, 0.1), color=0x00FF00, font_size=20)
        
        gui.show()
        time.sleep(0.03) # Cap FPS

    is_running = False