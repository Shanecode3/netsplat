import time
import math
from wifi_sensor import WifiScanner
from renderer import MapRenderer
from agent_brain import NetworkDoctor

def main():
    # 1. Start Subsystems
    print("Initializing Wi-Fi Sensor...")
    sensor = WifiScanner()
    sensor.start()
    
    print("Initializing AI Doctor...")
    doctor = NetworkDoctor()
    doctor.start()
    
    print("Opening Graphics Window...")
    renderer = MapRenderer()
    
    # 2. Robot State
    robot_x = 400.0
    robot_y = 300.0
    robot_angle = 0.0
    speed = 3.0
    
    print("--- SYSTEM READY ---")
    print("CLICK THE GRAPHICS WINDOW TO FOCUS IT.")
    print("Controls: W (Forward), A (Left), D (Right), S (Back)")
    
    last_record_time = 0
    
    while renderer.is_active():
        gui = renderer.get_input()
        
        # CRITICAL FIX: Flush the event queue so keys register
        while gui.get_event():
            pass
        
        # --- INPUT HANDLING ---
        moved = False
        if gui.is_pressed('w'):
            robot_x += math.cos(robot_angle) * speed
            robot_y += math.sin(robot_angle) * speed
            moved = True
        
        if gui.is_pressed('s'):
            robot_x -= math.cos(robot_angle) * speed
            robot_y -= math.sin(robot_angle) * speed
            moved = True
            
        if gui.is_pressed('a'):
            robot_angle += 0.05
            moved = True
            
        if gui.is_pressed('d'):
            robot_angle -= 0.05
            moved = True
            
        if gui.is_pressed(gui.SPACE):
            speed = 6.0
        else:
            speed = 3.0

        # Debug Print: Prove the keys are working
        if moved:
            print(f"Moving: {int(robot_x)}, {int(robot_y)} | Angle: {robot_angle:.2f}")

        # --- DATA RECORDING ---
        if time.time() - last_record_time > 0.2:
            current_signal = sensor.current_rssi
            renderer.add_point(robot_x, robot_y, current_signal)
            doctor.add_reading(current_signal)
            last_record_time = time.time()

        # --- DRAW FRAME ---
        renderer.render(robot_x, robot_y)
        
        # HUD
        gui.text(f"Signal: {sensor.current_rssi} dBm", pos=(0.05, 0.95), color=0xFFFFFF, font_size=24)
        gui.text(f"Pos: {int(robot_x)}, {int(robot_y)}", pos=(0.05, 0.90), color=0xAAAAAA, font_size=20)
        
        # AI Diagnosis (Green)
        gui.text(f"AI: {doctor.latest_diagnosis}", pos=(0.05, 0.1), color=0x00FF00, font_size=28)
        
        renderer.show()

    # Cleanup
    sensor.stop()
    doctor.stop()

if __name__ == "__main__":
    main()