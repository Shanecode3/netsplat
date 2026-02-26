import time
from wifi_sensor import WifiScanner
from renderer import MapRenderer
from agent_brain import NetworkDoctor
from location_tracker import LocationSensor

def main():
    sensor = WifiScanner()
    sensor.start()
    
    location = LocationSensor()
    location.start()
    
    doctor = NetworkDoctor()
    doctor.start()
    
    renderer = MapRenderer()
    
    last_record_time = 0
    
    while renderer.is_active():
        gui = renderer.get_input()
        
        while gui.get_event():
            pass

        robot_x = location.x
        robot_y = location.y

        if location.status == "Tracking" and time.time() - last_record_time > 0.2:
            current_signal = sensor.current_rssi
            renderer.add_point(robot_x, robot_y, current_signal)
            doctor.add_reading(current_signal)
            last_record_time = time.time()

        renderer.render(robot_x, robot_y)
        
        gui.text(f"Signal: {sensor.current_rssi} dBm", pos=(0.05, 0.95), color=0xFFFFFF, font_size=24)
        gui.text(f"Pos: {int(robot_x)}, {int(robot_y)}", pos=(0.05, 0.90), color=0xAAAAAA, font_size=20)
        
        status_color = 0x00FF00 if location.status == "Tracking" else 0xFF0000
        gui.text(f"Camera: {location.status}", pos=(0.05, 0.85), color=status_color, font_size=20)
        
        gui.text(f"AI: {doctor.latest_diagnosis}", pos=(0.05, 0.1), color=0x00FF00, font_size=28)
        
        renderer.show()

    sensor.stop()
    location.stop()
    doctor.stop()

if __name__ == "__main__":
    main()