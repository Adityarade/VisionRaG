import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
import os
from functools import lru_cache
from dotenv import load_dotenv
import torch

# Ultimate fix for PyTorch 2.6+ unpickling errors with YOLO
# We monkey-patch torch.load to default to weights_only=False
_original_torch_load = torch.load
def safe_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = safe_torch_load

load_dotenv()
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")

@lru_cache(maxsize=1)
def get_yolo_model():
    """Caches the YOLO model in memory to prevent reloading"""
    return YOLO(YOLO_MODEL_PATH)

def detect_objects(image: Image.Image, conf_threshold: float = 0.25):
    """
    Runs YOLOv8 object detection on a PIL image.
    Returns:
    - annotated_img: PIL Image with bounding boxes
    - detection_summary: string
    - detected_objects: list of dictionaries with class name, conf, bbox
    """
    model = get_yolo_model()
    
    # Convert PIL to cv2 for drawing and model input
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Run inference with confidence threshold and reduced image size for speed
    results = model(img_cv, conf=conf_threshold, imgsz=320)
    result = results[0]
    
    detected_objects = []
    summary_parts = []
    
    # We will use Ultralytics plot() for a clean annotated image
    annotated_img_cv = result.plot()
    annotated_img = Image.fromarray(cv2.cvtColor(annotated_img_cv, cv2.COLOR_BGR2RGB))
    
    for box in result.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        cls_name = model.names[cls_id]
        
        # Bounding box coords: xmin, ymin, xmax, ymax
        bbox = box.xyxy[0].tolist()
        
        detected_objects.append({
            "class": cls_name,
            "confidence": conf,
            "bbox": bbox
        })
        
        summary_parts.append(f"{cls_name}({conf:.2f})")
    
    detection_summary = "Detected: " + ", ".join(summary_parts) if summary_parts else "Detected: None"
    
    return annotated_img, detection_summary, detected_objects
