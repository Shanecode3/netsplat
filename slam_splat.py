import taichi as ti
import cv2
import numpy as np
import pywifi
import threading
import time

# --- CONFIGURATION ---
ti.init(arch=ti.gpu)
RES_X, RES_Y = 800, 600

# 1. SHARED STATE
current_rssi = -100.0
robot_x = 400.0
robot_y = 300.0
is_running = True

# 2. TAICHI FIELDS
max_points = 10000
path_history = ti.Vector.field(3, dtype=ti.f32, shape=max_points) # x, y, signal
point_counter = ti.field(dtype=ti.i32, shape=())
pixels = ti.Vector.field(3, dtype=ti.f32, shape=(RES_X, RES_Y))

# --- THREAD 1: WI-FI SCANNER ---
def wifi_scanner():
    global current_rssi
    wifi = pywifi.PyWiFi()
    if not wifi.interfaces(): return
    iface = wifi.interfaces()[0]
    
    while is_running:
        try:
            iface.scan()
            time.sleep(1.5)
            results = iface.scan_results()
            best = -100
            for n in results:
                if n.signal > best and n.signal < 0:
                    best = n.signal
            current_rssi = best
        except:
            time.sleep(1)

# --- THREAD 2: VISION TRACKER ---
#def vision_odometry():
 #   global robot_x, robot_y
 #   
 #   lk_params = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.03))
 #   feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)
    
 #   cap = cv2.VideoCapture(0)
 #   ret, old_frame = cap.read()
 #   if not ret: return
    
 #   old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
 #   p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
    
 #   while is_running:
 #       ret, frame = cap.read()
 #       if not ret: break
        
 #       frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
 #       if p0 is not None and len(p0) > 0:
 #           p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
            
 #           if p1 is not None:
 #               good_new = p1[st==1]
 #               good_old = p0[st==1]
                
 #               dx = 0
 #               dy = 0
 #               for i, (new, old) in enumerate(zip(good_new, good_old)):
 #                   a, b = new.ravel()
 #                   c, d = old.ravel()
 #                   dx += (c - a)
 #                   dy += (d - b)
                
 #               if len(good_new) > 0:
 #                   dx /= len(good_new)
 #                   dy /= len(good_new)
                
 #               scale = 0.05
 #               robot_x += dx * scale
 #               robot_y += dy * scale
                
 #               old_gray = frame_gray.copy()
 #               p0 = good_new.reshape(-1, 1, 2)
                
 #               if len(p0) < 50:
 #                    p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
        
 #       cv2.imshow("Tracking (Don't Close)", frame)
 #       if cv2.waitKey(1) == 27: break

 #   cap.release()
 #   cv2.destroyAllWindows()

 # --- THREAD 2: VISION TRACKER (OPTIMIZED) ---
def vision_odometry():
    global robot_x, robot_y
    
    # 1. FASTER SETTINGS (Lower quality, higher speed)
    # We use a smaller window (15x15) because we will shrink the image
    lk_params = dict(winSize=(15, 15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
    
    # Track more points (200) but with less strict quality
    feature_params = dict(maxCorners=200, qualityLevel=0.1, minDistance=5, blockSize=5)
    
    cap = cv2.VideoCapture(0)
    
    # Force Camera to Low Resolution (Critical for FPS)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
    ret, old_frame = cap.read()
    if not ret: return
    
    # Working at 320x240 is 10x faster than 1080p
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
    
    while is_running:
        ret, frame = cap.read()
        if not ret: break
        
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if p0 is not None and len(p0) > 0:
            p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
            
            if p1 is not None:
                good_new = p1[st==1]
                good_old = p0[st==1]
                
                dx_total = 0
                dy_total = 0
                count = 0
                
                # MOVEMENT FILTERING
                for i, (new, old) in enumerate(zip(good_new, good_old)):
                    a, b = new.ravel()
                    c, d = old.ravel()
                    
                    diff_x = c - a
                    diff_y = d - b
                    
                    # OUTLIER REJECTION:
                    # If a single point moves > 20 pixels, it's probably a glitch (or a bird flying by). Ignore it.
                    if abs(diff_x) < 20 and abs(diff_y) < 20:
                        dx_total += diff_x
                        dy_total += diff_y
                        count += 1
                
                if count > 0:
                    dx = dx_total / count
                    dy = dy_total / count
                    
                    # DEAD ZONE (The "Steady Hand" Filter)
                    if abs(dx) < 0.2: dx = 0
                    if abs(dy) < 0.2: dy = 0
                    
                    # TUNING:
                    # Lower resolution means pixels represent bigger area.
                    # We use a smaller scale factor.
                    scale = 0.5 
                    
                    # Rotation Compensation:
                    # When you turn the laptop, the image slides horizontally.
                    # We dampen X axis movement more than Y axis to prevent "Spinning = Walking"
                    robot_x += dx * scale * 0.8  # Dampen turning
                    robot_y += dy * scale        # Full speed forward/back
                
                old_gray = frame_gray.copy()
                p0 = good_new.reshape(-1, 1, 2)
                
                # Re-seed points often
                if len(p0) < 100:
                     p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
        
        # Optional: Show what the robot sees
        # cv2.imshow("Robot Eyes (320x240)", frame)
        # if cv2.waitKey(1) == 27: break

    cap.release()
    cv2.destroyAllWindows()

# --- MAIN THREAD: GPU RENDERER (FIXED) ---
@ti.kernel
def render_map(count: ti.i32):
    # 1. Clear Screen (Parallel across pixels)
    for i, j in pixels:
        pixels[i, j] = ti.Vector([0.05, 0.05, 0.05])

    # 2. Draw Points (Serial across points)
    for k in range(count):
        # Get Center
        cx = int(path_history[k].x)
        cy = int(path_history[k].y)
        sig = path_history[k].z
        
        # Color Math
        norm = (sig - -90.0) / 50.0
        norm = ti.max(0.0, ti.min(1.0, norm))
        color = ti.Vector([1.0 - norm, norm, 0.0])
        
        # Draw Circle manually (Loops over small 10x10 box only)
        # This is valid because 'range' is serial, not parallel 'struct_for'
        radius = 5
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy < radius*radius:
                    # Boundary Check
                    if cx + dx >= 0 and cx + dx < RES_X and cy + dy >= 0 and cy + dy < RES_Y:
                        pixels[cx + dx, cy + dy] = color
    
    # 3. Draw Current Robot (White Dot)
    if count > 0:
        curr_x = int(path_history[count-1].x)
        curr_y = int(path_history[count-1].y)
        for dy in range(-7, 8):
            for dx in range(-7, 8):
                if dx*dx + dy*dy < 49:
                    if curr_x + dx >= 0 and curr_x + dx < RES_X and curr_y + dy >= 0 and curr_y + dy < RES_Y:
                        pixels[curr_x + dx, curr_y + dy] = ti.Vector([1.0, 1.0, 1.0])

if __name__ == "__main__":
    t1 = threading.Thread(target=wifi_scanner, daemon=True)
    t1.start()
    
    t2 = threading.Thread(target=vision_odometry, daemon=True)
    t2.start()
    
    gui = ti.GUI("SLAM-Splat: Heatmap Generator", res=(RES_X, RES_Y))
    
    print("--- SYSTEM READY ---")
    
    last_record_time = 0
    
    while gui.running:
        # Record Data Point
        if time.time() - last_record_time > 0.1:
            idx = point_counter[None]
            if idx < max_points:
                path_history[idx].x = robot_x
                path_history[idx].y = robot_y
                path_history[idx].z = current_rssi
                point_counter[None] += 1
            last_record_time = time.time()
        
        render_map(point_counter[None])
        gui.set_image(pixels)
        
        gui.text(f"Signal: {current_rssi} dBm", pos=(0.05, 0.95), color=0xFFFFFF, font_size=24)
        gui.show()
    
    is_running = False