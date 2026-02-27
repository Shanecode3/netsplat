import threading
import time
import ollama
from collections import deque

class NetworkDoctor:
    def __init__(self, model="llama3"):
        self.model = model
        self.history = deque(maxlen=20) # Short-term memory
        self.latest_diagnosis = "Initializing AI..."
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._brain_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def add_reading(self, rssi):
        # Main loop call to feed data
        self.history.append(rssi)

    def _brain_loop(self):
        print("🧠 AI Doctor is Online.")
        
        # Initial wait to gather data so the first diagnosis isn't just "No Data"
        time.sleep(5)
        
        while self.running:
            if len(self.history) > 10:
                try:
                    # Prepare the Patient Data for the AI
                    data_str = str(list(self.history))
                    
                    # Consult the AI (Llama 3)
                    response = ollama.chat(model=self.model, messages=[
                        {'role': 'system', 'content': "You are a Wi-Fi Diagnostic Tool. Analyze the RSSI dBm history. -90 is bad, -30 is good. Sudden drops mean interference. Output ONLY a 5-word status report."},
                        {'role': 'user', 'content': f"Data: {data_str}"}
                    ])
                    
                    # Update with the AI's latest diagnosis
                    self.latest_diagnosis = response['message']['content']
                    
                except Exception as e:
                    print(f"AI Error: {e}")
                    self.latest_diagnosis = "AI Offline (Check Ollama)"
            
            # To avoid unneccessary overloading of the GPU. Diagnosis limited to every 10 seconds.
            time.sleep(10)
    
    def calculate_optimal_placement(self, path_data, r1_coords, r2_coords):
        print("\n🧠 AI Analyzing Room Topology...")
        self.latest_diagnosis = "Analyzing RF Topology..."
        
        # Feature Engineering: Isolating the Dead Zones (Signal < -75)
        dead_zones = [pt for pt in path_data if pt['signal'] < -75]
        
        if not dead_zones:
            self.latest_diagnosis = "Coverage is perfect. No changes needed."
            print("No significant dead zones detected yet. Keep walking!")
            return None
            
        # Find the "Center of Mass" of the dead zones
        avg_x = sum(pt['x'] for pt in dead_zones) / len(dead_zones)
        avg_y = sum(pt['y'] for pt in dead_zones) / len(dead_zones)
        
        # Prompt Llama 3 with the data
        prompt = f"""
        You are an Enterprise RF Engineer. 
        Current Setup: Router 1 at {r1_coords}, Router 2 at {r2_coords}.
        A massive dead zone cluster is centered at Coordinates (X:{int(avg_x)}, Y:{int(avg_y)}).
        
        Provide a 1-sentence recommendation on where to physically move the routers to cover this dead zone. 
        Keep it highly technical.
        """
        
        try:
            import ollama 
            response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': prompt}])
            
            # Update HUD (truncated)
            self.latest_diagnosis = response['message']['content'][:80] + "..." 
            print(f"\n📊 LLAMA 3 REPORT:\n{response['message']['content']}\n")
            
            # Return the geometric coordinates to Taichi
            return (avg_x, avg_y) 
            
        except Exception as e:
            print(f"AI Error: {e}")
            self.latest_diagnosis = "AI Core Offline."
            return None