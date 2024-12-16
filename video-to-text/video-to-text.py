import torch
import cv2
import paho.mqtt.client as mqtt
import os
import time
from pathlib import Path

# MQTT Configuration
MQTT_BROKER = "h7349222.ala.eu-central-1.emqxsl.com"
MQTT_PORT = 8883
MQTT_TOPIC = "emqx/objects"
MQTT_USERNAME = "chatadoriana"
MQTT_PASSWORD = "chatadoriana"
CERT_FILE = "emqxsl-ca.crt"  # SSL Certificate for secure communication

# YOLOv5 Model Configuration
MODEL_PATH = "yolov5m.pt"  # Path to YOLOv5 model
YOLOV5_DIR = "yolov5"  # Path to YOLOv5 directory

# Add YOLOv5 to the Python path
import sys
sys.path.insert(0, YOLOV5_DIR)

from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device

# Select device (CPU or GPU)
device = select_device('')
model = DetectMultiBackend(MODEL_PATH, device=device)

# MQTT Client Setup
def publish_message(message):
    try:
        client = mqtt.Client()
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.tls_set(CERT_FILE)  # Enable SSL for secure connection
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        result = client.publish(MQTT_TOPIC, message)
        if result[0] != mqtt.MQTT_ERR_SUCCESS:
            print("Error: Failed to publish message.")
        else:
            print(f"Published: {message}")
        client.disconnect()
    except Exception as e:
        print(f"Error connecting to MQTT: {e}")

# Detect objects from webcam stream
def process_video_from_webcam():
    cap = cv2.VideoCapture(0)  # Use webcam (device 0)
    last_published_time = time.time()  # Track last MQTT publish time

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to read from webcam. Exiting...")
            break

        # Prepare frame for YOLO model
        img = torch.from_numpy(frame).permute(2, 0, 1).float() / 255.0
        img = img.unsqueeze(0)

        # Run YOLOv5 model
        results = model(img)
        detections = non_max_suppression(results, conf_thres=0.25, iou_thres=0.45)[0]

        labels = []
        largest_box = None
        if detections is not None and len(detections):
            # Adjust bounding boxes to frame size
            detections[:, :4] = scale_boxes(img.shape[2:], detections[:, :4], frame.shape).round()

            # Find the largest detected object
            largest_area = 0
            largest_label = None
            for *xyxy, conf, cls in detections:
                x1, y1, x2, y2 = map(int, xyxy)  # Bounding box coordinates
                area = (x2 - x1) * (y2 - y1)  # Calculate area of the bounding box
                if area > largest_area:
                    largest_area = area
                    largest_label = model.names[int(cls)]  # Class name
                    largest_box = (x1, y1, x2, y2, largest_label)

            if largest_label:
                labels.append(largest_label)

        # Draw the bounding box for the largest object
        if largest_box:
            x1, y1, x2, y2, label = largest_box
            color = (0, 255, 0)  # Green color for the bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            # Publish the detected object every 2 seconds
            if time.time() - last_published_time > 2:
                publish_message(label)
                last_published_time = time.time()

        # Display the live webcam feed with YOLO detections
        cv2.imshow("YOLOv5 Video Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Exit on pressing 'q'
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    process_video_from_webcam()
