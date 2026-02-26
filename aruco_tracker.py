import cv2
import cv2.aruco as aruco
import numpy as np

def track_base_station():
    cap = cv2.VideoCapture(0)
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
    parameters = aruco.DetectorParameters()
    detector = aruco.ArucoDetector(dictionary, parameters)

    print("--- SEARCHING FOR BASE STATION ---")
    print("Point laptop camera at your phone screen.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = detector.detectMarkers(gray)

        if ids is not None and 1 in ids:
            index = np.where(ids == 1)[0][0]
            c = corners[index][0]
            
            # Draw the box
            cv2.polylines(frame, [c.astype(np.int32)], True, (0, 255, 0), 2)
            
            # Calculate Center
            center_x = int((c[0][0] + c[2][0]) / 2)
            center_y = int((c[0][1] + c[2][1]) / 2)
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
            
            # Calculate "Pseudo-Distance" based on pixel width
            pixel_width = np.linalg.norm(c[0] - c[1])
            estimated_distance_cm = 5000 / pixel_width
            
            cv2.putText(frame, f"Dist: {int(estimated_distance_cm)} cm", (center_x, center_y - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            print(f"📍 Locked. Dist: {int(estimated_distance_cm)}cm")

        cv2.imshow("ArUco Tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    track_base_station()