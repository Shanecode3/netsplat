from flask import Flask, request
import threading
import logging
import time
import math

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- SHARED MEMORY ---
shared_x = 960.0
shared_y = 540.0
current_yaw = 0.0
last_step_time = 0
prev_magnitude = 9.8 # <--- NEW: Stores the last reading to calculate the difference
shared_status = "Waiting for IMU..."

@app.route('/data', methods=['POST'])
def handle_data():
    global shared_x, shared_y, current_yaw, last_step_time, shared_status
    
    try:
        data = request.json
        payloads = data.get('payload', [])
        
        for item in payloads:
            sensor_name = item.get('name', '').lower()
            values = item.get('values', {})
            
            # 1. READ THE COMPASS
            if 'orientation' in sensor_name:
                if 'yaw' in values:
                    current_yaw = -values['yaw'] 
                    shared_status = "Tracking (IMU Active)"

            # 2. DETECT THE STEPS (Bulletproof Absolute Threshold)
            if 'accelerometer' in sensor_name or 'linearacceleration' in sensor_name:
                x, y, z = values.get('x', 0), values.get('y', 0), values.get('z', 0)
                
                # Calculate current total force
                m = math.sqrt(x**2 + y**2 + z**2)
                
                # IGNORE 0s and IGNORE resting gravity (9.8).
                # A step without gravity reads between 2.0 and 6.0
                # A step WITH gravity reads above 11.5
                if (2.0 < m < 6.0) or (m > 11.5):
                    
                    # Cooldown: You physically cannot take 2 steps in less than 0.4 seconds
                    if (time.time() - last_step_time) > 0.4:
                        
                        step_size_pixels = 30.0 # Your 1080p stride
                        
                        shared_x += step_size_pixels * math.cos(current_yaw)
                        shared_y += step_size_pixels * math.sin(current_yaw)
                        
                        last_step_time = time.time()
                        print(f"👣 Step! Force: {m:.2f} | Heading: {math.degrees(current_yaw):.0f}°")
                    
        return "Success", 200
    except Exception as e:
        return "Error", 500

class LocationSensor:
    def __init__(self):
        self.x = 960.0
        self.y = 540.0
        self.status = "Starting Server..."
        self.running = False

    def start(self):
        self.running = True
        server_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True)
        server_thread.start()
        
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