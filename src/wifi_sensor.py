import pywifi
import time
import threading

class WifiScanner:
    def __init__(self):
        self.current_rssi = -100.0
        self.running = False
        self.thread = None
        self.target_ssid = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _scan_loop(self):
        wifi = pywifi.PyWiFi()
        
        if len(wifi.interfaces()) == 0:
            print("Error: No Wi-Fi Interface Found.")
            return

        iface = wifi.interfaces()[0]
        
        while self.running:
            try:
                iface.scan()
                time.sleep(1.5) 
                
                results = iface.scan_results()
                
                # LOCK ONTO YOUR NETWORK
                if self.target_ssid is None:
                    best_initial_signal = -100
                    for network in results:
                        # Ignore hidden networks (empty SSID)
                        if network.signal > best_initial_signal and network.signal < 0 and network.ssid != "":
                            best_initial_signal = network.signal
                            self.target_ssid = network.ssid
                            
                    if self.target_ssid:
                        print(f"\n📡 Locked onto Target Network: '{self.target_ssid}'\n")

                # TRACK ONLY YOUR NETWORK
                if self.target_ssid is not None:
                    best_target_signal = -100
                    for network in results:
                        # Only check routers with your network name (can handle Mesh networks as well)
                        if network.ssid == self.target_ssid:
                            if network.signal > best_target_signal and network.signal < 0:
                                best_target_signal = network.signal
                    
                    self.current_rssi = best_target_signal
                
            except Exception as e:
                time.sleep(1)