import os
import io
import json
import torch
import numpy as np
from PIL import Image
from typing import Dict, Any, List
from ultralytics import YOLO
import easyocr
from transformers import BlipProcessor, BlipForConditionalGeneration

class LocalVisionEngine:
    """
    Core Logic for OFFLINE / LOCAL Visual Intelligence.
    Uses YOLOv8, BLIP-2, and EasyOCR.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalVisionEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        print("Initializing Local AI Models (YOLOv8, BLIP, EasyOCR)...")
        # Load YOLOv8 (smallest version for speed/demo)
        # It will download the .pt file on first run if not present
        self.yolo_model = YOLO('yolov8n.pt') 
        
        # Load BLIP (Image Captioning)
        # Using SalesForce/blip-image-captioning-base
        self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        
        # Load EasyOCR
        self.ocr_reader = easyocr.Reader(['en'])
        
        # Device management
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.blip_model.to(self.device)
        
        self._initialized = True
        print(f"Local AI Models loaded successfully on {self.device}.")

    def analyze_image(self, image_path: Image.Image) -> Dict[str, Any]:
        """
        Executes the 3-Step Offline Pipeline with Bounding Box Extraction.
        """
        img_array = np.array(image_path)
        width, height = image_path.size
        
        # --- STEP 1: Object Detection (YOLOv8) ---
        results = self.yolo_model(image_path, verbose=False)
        detected_objects = {}
        bounding_boxes = []
        
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.yolo_model.names[cls_id]
                conf = float(box.conf[0])
                
                # Update counts
                detected_objects[label] = detected_objects.get(label, 0) + 1
                
                # Extract normalized coordinates for bounding box
                xyxy = box.xyxy[0].tolist()
                bounding_boxes.append({
                    "label": label,
                    "confidence": conf,
                    "box": {
                        "top": f"{(xyxy[1]/height)*100}%",
                        "left": f"{(xyxy[0]/width)*100}%",
                        "width": f"{((xyxy[2]-xyxy[0])/width)*100}%",
                        "height": f"{((xyxy[3]-xyxy[1])/height)*100}%"
                    }
                })
        
        # --- STEP 2: Scene Description (BLIP) ---
        inputs = self.blip_processor(image_path, return_tensors="pt").to(self.device)
        out = self.blip_model.generate(**inputs)
        scene_description = self.blip_processor.decode(out[0], skip_special_tokens=True)

        # --- STEP 3: Text Extraction (OCR) ---
        ocr_results = self.ocr_reader.readtext(img_array)
        text_detected = [res[1] for res in ocr_results]
        
        if not text_detected:
            text_detected = ["No readable text detected"]

        # --- HEURISTIC RISK ANALYSIS ---
        risks = []
        if any(obj in detected_objects for obj in ["fire", "smoke", "knife"]):
            risks.append("Immediate physical hazard detected.")
        if any(item in detected_objects for item in ["gas", "leak", "danger"]):
            risks.append("Structural hazard or chemical indicator detected.")
        
        return {
            "analysis_mode": "Offline Local AI",
            "scene_description": scene_description,
            "detected_objects": detected_objects,
            "bounding_boxes": bounding_boxes[:10], # Limit for demo
            "text_detected": text_detected,
            "risk_assessment": " ".join(risks) if risks else "Standard environment. No high-risk anomalies detected.",
            "spatial_metrics": {
                "object_count": sum(detected_objects.values()),
                "unique_labels": len(detected_objects),
                "text_elements": len(text_detected) if text_detected and text_detected[0] != "No readable text detected" else 0,
                "complexity_score": (sum(detected_objects.values()) * 0.5) + (len(text_detected) * 0.2)
            },
            "confidence_note": "Analysis performed using YOLOv8 + BLIP + EasyOCR"
        }

class ImagePreProcessingLayer:
    """Layer 3: Image Pre-Processing"""
    
    def process(self, image_data: bytes) -> Image.Image:
        try:
            image = Image.open(io.BytesIO(image_data))
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Keep original for better OCR/Detection but cap at reasonable size
            max_size = 1200
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
        except Exception as e:
            raise ValueError(f"Image processing failed: {str(e)}")

class VisionProcessingLayer:
    """Layer 4: Unified Local Engine"""
    
    def __init__(self):
        self.engine = None

    async def analyze(self, image: Image.Image) -> Dict[str, Any]:
        """
        Main entry for Layer 4 analysis.
        Initializes engine on first request.
        """
        if self.engine is None:
            self.engine = LocalVisionEngine()
            
        try:
            return self.engine.analyze_image(image)
        except Exception as e:
            print(f"Local Analysis Failed: {str(e)}")
            return {
                "analysis_mode": "Offline Local AI (Failsafe)",
                "scene_description": "Scene analysis unavailable.",
                "detected_objects": {},
                "text_detected": ["Error during local processing"],
                "confidence_note": f"Failsafe mode triggered: {str(e)}"
            }

class VisualContextSummarizationLayer:
    """Layer 5: Local Context Summarization"""
    
    def summarize(self, vision_data: Dict[str, Any]) -> str:
        """
        Convert detection results into a concise semantic summary for the UI.
        """
        desc = vision_data.get("scene_description", "Unknown scene")
        obj = vision_data.get("detected_objects", {})
        
        counts_list = [f"{count} {name}" for name, count in obj.items()]
        counts_str = ", ".join(counts_list) if counts_list else "no specific objects"
        
        return f"{desc}. Detected: {counts_str}."
