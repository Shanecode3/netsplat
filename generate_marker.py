import cv2
import numpy as np

# Load the dictionary that defines the markers
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

# Generate Marker ID #1 (Size: 400x400 pixels)
marker_image = np.zeros((400, 400), dtype=np.uint8)
marker_image = cv2.aruco.generateImageMarker(dictionary, 1, 400, marker_image, 1)

cv2.imwrite("marker_1.png", marker_image)
print("✅ Saved 'marker_1.png'. Send this to your phone and open it full screen.")