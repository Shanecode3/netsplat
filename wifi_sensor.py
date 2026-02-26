import pywifi
import time
import threading

class WifiScanner:
    def __init__(self):
        self.current_rssi = -100.0
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _scan_loop(self):
        wifi = pywifi.PyWiFi()
        
        if len(wifi.interfaces()) == 0:
            return

        iface = wifi.interfaces()[0]
        
        while self.running:
            try:
                iface.scan()
                time.sleep(1.0)
                
                results = iface.scan_results()
                best_signal = -100
                
                for network in results:
                    if network.signal > best_signal and network.signal < 0:
                        best_signal = network.signal
                
                self.current_rssi = best_signal
                
            except Exception:
                time.sleep(1)