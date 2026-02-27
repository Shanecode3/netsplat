import time
from src.wifi_sensor import WifiScanner
from src.renderer import MapRenderer
from src.agent_brain import NetworkDoctor
from src.location_tracker import LocationSensor

def main():
    print("Initializing Wi-Fi Sensor...")
    sensor = WifiScanner()
    sensor.start()
    
    print("Initializing PDR Location Tracking...")
    location = LocationSensor()
    location.start()
    
    print("Initializing AI Doctor...")
    doctor = NetworkDoctor()
    doctor.start()
    
    print("Opening Graphics Window...")
    renderer = MapRenderer()
    
    print("\n--- SYSTEM READY ---")
    print("1. Start 'Sensor Logger' on your phone.")
    print("2. Hold your phone flat (like a tray) and point it straight ahead.")
    print("3. Start walking.")
    
    last_record_time = 0
    
    while renderer.is_active():
        gui = renderer.get_input()
        
        # INPUT HANDLING
        for e in gui.get_events(gui.PRESS):
            if e.key == 'o' or e.key == 'O':
                renderer.toggle_optimization()
                
            elif e.key == '1':
                renderer.router_1[None] = [robot_x, robot_y]
                renderer.router_1_active[None] = 1
                print(f"Router 1 Marked at {int(robot_x)}, {int(robot_y)}")
                
            elif e.key == '2':
                renderer.router_2[None] = [robot_x, robot_y]
                renderer.router_2_active[None] = 1
                print(f"Router 2 Marked at {int(robot_x)}, {int(robot_y)}")
                
            # Taichi registers 'Enter' as gui.RETURN
            elif e.key == gui.RETURN or e.key == 'Return':
                print("Triggering AI Placement Optimization...")
                
                history_data = []
                for i in range(renderer.point_counter[None]):
                    history_data.append({
                        'x': renderer.path_history[i].x,
                        'y': renderer.path_history[i].y,
                        'signal': renderer.path_history[i].z
                    })
                
                r1 = (int(renderer.router_1[None].x), int(renderer.router_1[None].y)) if renderer.router_1_active[None] else "Not Set"
                r2 = (int(renderer.router_2[None].x), int(renderer.router_2[None].y)) if renderer.router_2_active[None] else "Not Set"
                
                # Run Llama 3 Analysis
                optimal_coords = doctor.calculate_optimal_placement(history_data, r1, r2)
                
                # Drop the Purple Star on the Map to show the optimal location for a new router
                if optimal_coords:
                    renderer.optimal_1[None] = [optimal_coords[0], optimal_coords[1]]
                    renderer.optimal_active[None] = 1

        # Pull real-world position from the IMU sensor's shared memory
        robot_x = location.x
        robot_y = location.y

        # Record data for the heatmap & AI
        if "Tracking" in location.status and time.time() - last_record_time > 0.2:
            current_signal = sensor.current_rssi
            renderer.add_point(robot_x, robot_y, current_signal)
            doctor.add_reading(current_signal)
            last_record_time = time.time()

        # Render Graphics
        renderer.render(robot_x, robot_y)
        
        # HUD
        gui.text(f"Signal: {sensor.current_rssi} dBm", pos=(0.05, 0.95), color=0xFFFFFF, font_size=24)
        gui.text(f"Pos: {int(robot_x)}, {int(robot_y)}", pos=(0.05, 0.90), color=0xAAAAAA, font_size=20)
        
        status_color = 0x00FF00 if "Tracking" in location.status else 0xFF0000
        gui.text(f"Tracker: {location.status}", pos=(0.05, 0.85), color=status_color, font_size=20)
        
        gui.text(f"AI: {doctor.latest_diagnosis}", pos=(0.05, 0.1), color=0x00FF00, font_size=28)
        
        renderer.show()

    sensor.stop()
    location.stop()
    doctor.stop()

if __name__ == "__main__":
    main()