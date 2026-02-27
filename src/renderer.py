import taichi as ti

ti.init(arch=ti.gpu)

RES_X, RES_Y = 1920, 1080

pixels = ti.Vector.field(3, dtype=ti.f32, shape=(RES_X, RES_Y))

max_points = 10000
path_history = ti.Vector.field(3, dtype=ti.f32, shape=max_points)
point_counter = ti.field(dtype=ti.i32, shape=())
# --- ROUTER MEMORY ---
router_1 = ti.Vector.field(2, dtype=ti.f32, shape=())
router_2 = ti.Vector.field(2, dtype=ti.f32, shape=())
router_1_active = ti.field(dtype=ti.i32, shape=())
router_2_active = ti.field(dtype=ti.i32, shape=())

optimal_1 = ti.Vector.field(2, dtype=ti.f32, shape=())
optimal_2 = ti.Vector.field(2, dtype=ti.f32, shape=())
optimal_active = ti.field(dtype=ti.i32, shape=())

# A toggle to show the raw dots or the optimized splat surface
show_optimized = ti.field(dtype=ti.i32, shape=())

@ti.kernel
def paint_raw_dots(count: ti.i32, robot_x: ti.f32, robot_y: ti.f32):
    # Clear screen
    for i, j in pixels:
        pixels[i, j] = ti.Vector([0.05, 0.05, 0.05])

    # Draw raw dots
    for k in range(count):
        cx = int(path_history[k].x)
        cy = int(path_history[k].y)
        sig = path_history[k].z
        
        norm = (sig - -90.0) / 50.0
        norm = ti.max(0.0, ti.min(1.0, norm))
        color = ti.Vector([1.0 - norm, norm, 0.0])
        
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                if 0 <= cx+dx < RES_X and 0 <= cy+dy < RES_Y:
                    pixels[cx+dx, cy+dy] = color

    # Draw Robot
    rx = int(robot_x)
    ry = int(robot_y)
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            if dx*dx + dy*dy < 25:
                if 0 <= rx+dx < RES_X and 0 <= ry+dy < RES_Y:
                    pixels[rx+dx, ry+dy] = ti.Vector([1.0, 1.0, 1.0])
    draw_routers()

@ti.kernel
def optimize_splat_surface(count: ti.i32):
    # This runs simultaneously for all 2,073,600 pixels on your GPU
    for i, j in pixels:
        total_weight = 0.0
        weighted_sig = 0.0
        
        # Look at every recorded data point
        for k in range(count):
            px = path_history[k].x
            py = path_history[k].y
            sig = path_history[k].z
            
            # Calculate distance squared
            dist_sq = (i - px)**2 + (j - py)**2
            
            # Optimization constraint: Only blend if within ~300 pixels (roughly 10 meters)
            if dist_sq < 10000.0:
                # Inverse Distance Weighting: Closer points matter more
                weight = 1.0 / (dist_sq + 1.0) 
                weighted_sig += sig * weight
                total_weight += weight
                
        # If the pixel is near our data, color it in
        if total_weight > 0.0:
            final_sig = weighted_sig / total_weight
            
            # Color Logic
            norm = (final_sig - -90.0) / 50.0
            norm = ti.max(0.0, ti.min(1.0, norm))
            pixels[i, j] = ti.Vector([1.0 - norm, norm, 0.0])
        else:
            # Empty space stays dark
            pixels[i, j] = ti.Vector([0.05, 0.05, 0.05])

    draw_routers()

@ti.func
def draw_routers():
    # Draw Router 1 (Cyan Square)
    if router_1_active[None] == 1:
        rx = int(router_1[None].x)
        ry = int(router_1[None].y)
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                if 0 <= rx+dx < RES_X and 0 <= ry+dy < RES_Y:
                    pixels[rx+dx, ry+dy] = ti.Vector([0.0, 1.0, 1.0])
                    
    # Draw Router 2 (Blue Square)
    if router_2_active[None] == 1:
        rx = int(router_2[None].x)
        ry = int(router_2[None].y)
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                if 0 <= rx+dx < RES_X and 0 <= ry+dy < RES_Y:
                    pixels[rx+dx, ry+dy] = ti.Vector([0.0, 0.5, 1.0])

    # Draw AI Suggestion (Purple Star)
    if optimal_active[None] == 1:
        ox = int(optimal_1[None].x)
        oy = int(optimal_1[None].y)
        for dy in range(-10, 11):
            for dx in range(-10, 11):
                # Draw a cross/star shape
                if abs(dx) < 3 or abs(dy) < 3:
                    if 0 <= ox+dx < RES_X and 0 <= oy+dy < RES_Y:
                        pixels[ox+dx, oy+dy] = ti.Vector([1.0, 0.0, 1.0])

class MapRenderer:
    def __init__(self):
        self.gui = ti.GUI("Signal-Splat Optimizer", res=(RES_X, RES_Y), fullscreen=False)
        show_optimized[None] = 0 # Default to raw dots
        self.router_1 = router_1
        self.router_2 = router_2
        self.router_1_active = router_1_active
        self.router_2_active = router_2_active
        self.optimal_1 = optimal_1
        self.optimal_active = optimal_active
        self.point_counter = point_counter
        self.path_history = path_history
        
    def add_point(self, x, y, signal):
        idx = point_counter[None]
        if idx < max_points:
            path_history[idx].x = x
            path_history[idx].y = y
            path_history[idx].z = signal
            point_counter[None] += 1
            
    def toggle_optimization(self):
        # Flips between 0 (Raw) and 1 (Optimized)
        show_optimized[None] = 1 - show_optimized[None]
        if show_optimized[None] == 1:
            print("🚀 GPU Optimization Phase Initialized...")
            
    def render(self, robot_x, robot_y):
        if show_optimized[None] == 0:
            paint_raw_dots(point_counter[None], robot_x, robot_y)
        else:
            # We don't draw the robot in optimized mode, just the clean map
            optimize_splat_surface(point_counter[None])
            
        self.gui.set_image(pixels)
    
    def show(self):
        self.gui.show()
        
    def is_active(self):
        return self.gui.running
        
    def get_input(self):
        return self.gui