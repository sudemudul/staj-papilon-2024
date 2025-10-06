import cv2
from ultralytics import YOLO
from PIL import Image
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best2.pt")

model = YOLO(MODEL_PATH)
def detect_banknote():
    webcam = cv2.VideoCapture(1)
    if not webcam.isOpened():
        print("Webcam could not be opened:(")
        return "Error! Webcam could not be opened."
    start_time = time.time()
    banknote = "0_liras"
    while(True):
        ret, frame = webcam.read()
        if not ret:
            print("Error in grabing frame:(")
            break
        results = model(frame,conf = 0.5)
        for result in results: 
            for cls in result.boxes.cls:
                banknote = model.names[int(cls)]
                break
        elapsed_time = time.time() - start_time
        if banknote != "0_liras" or elapsed_time > 5:
            break
    webcam.release()
    cv2.destroyAllWindows()
    return banknote
