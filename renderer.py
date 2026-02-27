import taichi as ti

ti.init(arch=ti.gpu)

RES_X, RES_Y = 1920, 1080

pixels = ti.Vector.field(3, dtype=ti.f32, shape=(RES_X, RES_Y))

max_points = 10000
path_history = ti.Vector.field(3, dtype=ti.f32, shape=max_points)
point_counter = ti.field(dtype=ti.i32, shape=())

@ti.kernel
def paint_heatmap(count: ti.i32, robot_x: ti.f32, robot_y: ti.f32):
    for i, j in pixels:
        pixels[i, j] = ti.Vector([0.05, 0.05, 0.05])

    for k in range(count):
        cx = int(path_history[k].x)
        cy = int(path_history[k].y)
        sig = path_history[k].z
        
        norm = (sig - -90.0) / 50.0
        norm = ti.max(0.0, ti.min(1.0, norm))
        color = ti.Vector([1.0 - norm, norm, 0.0])
        
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if cx+dx >= 0 and cx+dx < RES_X and cy+dy >= 0 and cy+dy < RES_Y:
                    pixels[cx+dx, cy+dy] = color

    rx = int(robot_x)
    ry = int(robot_y)
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            if dx*dx + dy*dy < 25:
                if rx+dx >= 0 and rx+dx < RES_X and ry+dy >= 0 and ry+dy < RES_Y:
                    pixels[rx+dx, ry+dy] = ti.Vector([1.0, 1.0, 1.0])

class MapRenderer:
    def __init__(self):
        self.gui = ti.GUI("Signal Mapper: Manual Mode", res=(RES_X, RES_Y))
        
    def add_point(self, x, y, signal):
        idx = point_counter[None]
        if idx < max_points:
            path_history[idx].x = x
            path_history[idx].y = y
            path_history[idx].z = signal
            point_counter[None] += 1
            
    def render(self, robot_x, robot_y):
        paint_heatmap(point_counter[None], robot_x, robot_y)
        self.gui.set_image(pixels)
    
    def show(self):
        self.gui.show()
        
    def is_active(self):
        return self.gui.running
        
    def get_input(self):
        return self.gui