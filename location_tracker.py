import cv2
import cv2.aruco as aruco
import numpy as np
import threading

class LocationSensor:
    def __init__(self):
        self.x = 400.0
        self.y = 50.0
        self.running = False
        self.thread = None
        self.status = "Searching..."

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._track_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _track_loop(self):
        cap = cv2.VideoCapture(0)
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
        parameters = aruco.DetectorParameters()
        detector = aruco.ArucoDetector(dictionary, parameters)

        focal_length = 1200.0
        center_x, center_y = 960, 540
        camera_matrix = np.array([
            [focal_length, 0, center_x],
            [0, focal_length, center_y],
            [0, 0, 1]
        ], dtype=float)
        dist_coeffs = np.zeros((4, 1))

        marker_length = 0.05

        obj_points = np.array([
            [-marker_length/2, marker_length/2, 0],
            [marker_length/2, marker_length/2, 0],
            [marker_length/2, -marker_length/2, 0],
            [-marker_length/2, -marker_length/2, 0]
        ], dtype=np.float32)

        while self.running:
            ret, frame = cap.read()
            if not ret: continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, rejected = detector.detectMarkers(gray)

            if ids is not None and 1 in ids:
                self.status = "Tracking"
                idx = np.where(ids == 1)[0][0]
                img_points = corners[idx][0]

                success, rvec, tvec = cv2.solvePnP(obj_points, img_points, camera_matrix, dist_coeffs)

                if success:
                    real_x = tvec[0][0] * 100
                    real_z = tvec[2][0] * 100

                    scale = 2.0
                    
                    self.x = 400.0 - (real_x * scale)
                    self.y = 50.0 + (real_z * scale)
            else:
                self.status = "Lost"

        cap.release()