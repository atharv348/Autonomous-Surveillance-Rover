import cv2
import numpy as np
from ultralytics import YOLO
import time

class AIVision:
    def __init__(self):
        print("🤖 Loading YOLOv8 model...")
        self.model = YOLO('models/yolov8n.pt')
        print("✅ YOLOv8 model loaded successfully")
        
        self.confidence_threshold = 0.5
        self.enabled = True
        self.current_detections = []
        self.total_detections = 0
        self.fps = 0
        self.class_names = self.model.names
    
    def process_frame(self, frame):
        if not self.enabled:
            return frame, []
        
        start_time = time.time()
        
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.class_names[class_id]
                
                detection = {
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                }
                detections.append(detection)
                
                color = self._get_color(class_id)
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                label = f"{class_name} {confidence:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(frame, (int(x1), int(y1) - label_size[1] - 10),
                            (int(x1) + label_size[0], int(y1)), color, -1)
                cv2.putText(frame, label, (int(x1), int(y1) - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        self.fps = 1.0 / (time.time() - start_time)
        
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Detections: {len(detections)}", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        self.current_detections = detections
        self.total_detections += len(detections)
        
        return frame, detections
    
    def _get_color(self, class_id):
        np.random.seed(class_id)
        return tuple(np.random.randint(0, 255, 3).tolist())
    
    def get_statistics(self):
        return {
            'current_detections': len(self.current_detections),
            'total_detections': self.total_detections,
            'fps': self.fps,
            'enabled': self.enabled
        }
    
    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
    
    def set_confidence(self, confidence):
        self.confidence_threshold = max(0.0, min(1.0, confidence))
