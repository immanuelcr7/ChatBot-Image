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
        Executes the 3-Step Offline Pipeline.
        """
        # Convert PIL to format YOLO and OCR like
        img_array = np.array(image_path)
        
        # --- STEP 1: Object Detection (YOLOv8) ---
        results = self.yolo_model(image_path, verbose=False)
        detected_objects = {
            "car": 0,
            "person": 0,
            "bike": 0,
            "others": []
        }
        
        others_seen = set()
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = self.yolo_model.names[cls_id]
                
                if label == "car":
                    detected_objects["car"] += 1
                elif label == "person":
                    detected_objects["person"] += 1
                elif label in ["bicycle", "motorcycle"]:
                    detected_objects["bike"] += 1
                else:
                    others_seen.add(label)
        
        detected_objects["others"] = list(others_seen)

        # --- STEP 2: Scene Description (BLIP) ---
        inputs = self.blip_processor(image_path, return_tensors="pt").to(self.device)
        out = self.blip_model.generate(**inputs)
        scene_description = self.blip_processor.decode(out[0], skip_special_tokens=True)

        # --- STEP 3: Text Extraction (OCR) ---
        # EasyOCR expects a path or a numpy array
        ocr_results = self.ocr_reader.readtext(img_array)
        text_detected = [res[1] for res in ocr_results]
        
        if not text_detected:
            text_detected = ["No readable text detected"]

        # --- FINAL JSON STRUCTURE ---
        return {
            "analysis_mode": "Offline Local AI",
            "scene_description": scene_description,
            "detected_objects": detected_objects,
            "text_detected": text_detected,
            "confidence_note": "Analysis performed using YOLOv8 + BLIP-2 + OCR without external APIs"
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
                "detected_objects": {"car": 0, "person": 0, "bike": 0, "others": []},
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
        counts = f"{obj.get('car', 0)} cars, {obj.get('person', 0)} people"
        
        return f"{desc}. Detected: {counts}."
