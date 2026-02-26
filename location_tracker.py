from flask import Flask, request
import threading
import logging
import time

# --- FLASK WEB SERVER (The Catching Mitt) ---
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) # Mute server logs so they don't flood your terminal

# Global variables to pass data to the Taichi loop
shared_x = 400.0
shared_y = 300.0
shared_status = "Waiting for Phone..."

@app.route('/data', methods=['POST'])
def handle_data():
    global shared_x, shared_y, shared_status
    
    try:
        data = request.json
        payloads = data.get('payload', [])
        
        for item in payloads:
            sensor_name = item.get('name', '').lower()
            
            # Look for the AR tracking data packet
            if 'ar' in sensor_name or 'pose' in sensor_name:
                values = item.get('values', {})
                
                # AR systems measure in real-world meters.
                # X is left/right. Z is forward/backward.
                if 'x' in values and 'z' in values:
                    scale = 80.0 # 80 pixels per meter of walking
                    
                    shared_x = 400.0 + (values['x'] * scale)
                    shared_y = 300.0 + (values['z'] * scale) 
                    shared_status = "Tracking (AR Bridge)"
                    
        return "Success", 200
    except Exception as e:
        return "Error", 500

# --- THE SENSOR CLASS (Matches your existing architecture) ---
class LocationSensor:
    def __init__(self):
        self.x = 400.0
        self.y = 300.0
        self.status = "Starting Server..."
        self.running = False

    def start(self):
        self.running = True
        
        # Start Flask server in the background (0.0.0.0 exposes it to your local network)
        server_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True)
        server_thread.start()
        
        # Start the updater
        update_thread = threading.Thread(target=self._update_loop, daemon=True)
        update_thread.start()

    def _update_loop(self):
        global shared_x, shared_y, shared_status
        while self.running:
            self.x = shared_x
            self.y = shared_y
            self.status = shared_status
            time.sleep(0.05)

    def stop(self):
        self.running = False