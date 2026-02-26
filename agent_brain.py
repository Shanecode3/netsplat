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
        # Main loop calls this to feed data
        self.history.append(rssi)

    def _brain_loop(self):
        print("🧠 AI Doctor is Online.")
        
        # Initial wait to gather data
        time.sleep(5)
        
        while self.running:
            if len(self.history) > 10:
                try:
                    # 1. Prepare the Patient Data
                    data_str = str(list(self.history))
                    
                    # 2. Consult the Specialist (Llama 3)
                    response = ollama.chat(model=self.model, messages=[
                        {'role': 'system', 'content': "You are a Wi-Fi Diagnostic Tool. Analyze the RSSI dBm history. -90 is bad, -30 is good. Sudden drops mean interference. Output ONLY a 5-word status report."},
                        {'role': 'user', 'content': f"Data: {data_str}"}
                    ])
                    
                    # 3. Update the Prescription
                    self.latest_diagnosis = response['message']['content']
                    
                except Exception as e:
                    print(f"AI Error: {e}")
                    self.latest_diagnosis = "AI Offline (Check Ollama)"
            
            # Don't burn the GPU. Diagnosis every 10 seconds is enough.
            time.sleep(10)