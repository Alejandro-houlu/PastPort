import asyncio
import base64
import io
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from typing import Dict, List, Optional, Union, Tuple
import json
import os
from pathlib import Path


class MainCamRecognitionService:
    """Main camera recognition service supporting YOLO segmentation models"""
    
    def __init__(self):
        self.models: Dict[str, YOLO] = {}
        self.model_path = Path(__file__).parent.parent / "ml_models"
        self.supported_models = [
            "yolo11n-seg.pt",
            "yolo11s-seg.pt", 
            "yolo11m-seg.pt",
            "yolo11l-seg.pt",
            "yolo11x-seg.pt",
            "yolo11n-seg-custom-v7.pt"
        ]
        self.default_model = "yolo11n-seg-custom-v7.pt"
        
    async def load_model(self, model_name: str) -> YOLO:
        """Load YOLO model asynchronously"""
        if model_name not in self.models:
            print(f"🤖 MainCam Service: Loading new model '{model_name}'")
            
            if model_name not in self.supported_models:
                print(f"❌ MainCam Service: Unsupported model: {model_name}")
                raise ValueError(f"Unsupported model: {model_name}")
            
            model_file_path = self.model_path / model_name
            if not model_file_path.exists():
                print(f"❌ MainCam Service: Model file not found: {model_file_path}")
                raise FileNotFoundError(f"Model file not found: {model_file_path}")
            
            print(f"📂 MainCam Service: Loading model from {model_file_path}")
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(None, YOLO, str(model_file_path))
            self.models[model_name] = model
            print(f"✅ MainCam Service: Model '{model_name}' loaded successfully")
        else:
            print(f"♻️ MainCam Service: Using cached model '{model_name}'")
            
        return self.models[model_name]
    
    async def process_image_data(self, image_data: Union[str, bytes, np.ndarray]) -> np.ndarray:
        """Convert various image input formats to numpy array"""
        if isinstance(image_data, str):
            print("📥 MainCam Service: Processing base64 string image data")
            # Base64 encoded image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
                print("🔍 MainCam Service: Stripped data URL prefix")
            
            image_bytes = base64.b64decode(image_data)
            print(f"📊 MainCam Service: Decoded {len(image_bytes)} bytes from base64")
            image = Image.open(io.BytesIO(image_bytes))
            array = np.array(image)
            print(f"🖼️ MainCam Service: Converted to numpy array shape: {array.shape}")
            return array
            
        elif isinstance(image_data, bytes):
            print(f"📥 MainCam Service: Processing raw bytes ({len(image_data)} bytes)")
            # Raw bytes
            image = Image.open(io.BytesIO(image_data))
            array = np.array(image)
            print(f"🖼️ MainCam Service: Converted to numpy array shape: {array.shape}")
            return array
            
        elif isinstance(image_data, np.ndarray):
            print(f"📥 MainCam Service: Using existing numpy array shape: {image_data.shape}")
            # Already numpy array
            return image_data
            
        else:
            print(f"❌ MainCam Service: Unsupported image data format: {type(image_data)}")
            raise ValueError("Unsupported image data format")
    
    async def predict_segmentation(
        self, 
        image_data: Union[str, bytes, np.ndarray],
        model_name: str = None,
        confidence: float = 0.25,
        iou_threshold: float = 0.45
    ) -> Dict:
        """Perform segmentation prediction on image"""
        if model_name is None:
            model_name = self.default_model
            
        print(f"🎯 MainCam Service: Starting prediction with model '{model_name}', conf={confidence}, iou={iou_threshold}")
        
        # Load model
        model = await self.load_model(model_name)
        
        # Process image
        image_array = await self.process_image_data(image_data)
        
        print(f"🚀 MainCam Service: Running YOLO inference on {image_array.shape} image")
        # Run prediction in thread pool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, 
            lambda: model.predict(
                image_array, 
                conf=confidence,
                iou=iou_threshold,
                verbose=False
            )
        )
        
        print("📋 MainCam Service: Formatting prediction results")
        formatted_results = await self._format_results(results[0], image_array.shape)
        
        detections = formatted_results["metadata"]["num_detections"]
        processing_time = formatted_results["metadata"]["processing_time"]
        print(f"✅ MainCam Service: Prediction complete - {detections} detections in {processing_time:.1f}ms")
        
        return formatted_results
    
    async def _format_results(self, result, image_shape: Tuple[int, int, int]) -> Dict:
        """Format YOLO results into JSON-serializable format"""
        formatted_result = {
            "image_shape": {
                "height": image_shape[0],
                "width": image_shape[1],
                "channels": image_shape[2] if len(image_shape) == 3 else 1
            },
            "detections": [],
            "masks": [],
            "metadata": {
                "num_detections": 0,
                "processing_time": getattr(result, 'speed', {}).get('preprocess', 0) + 
                                getattr(result, 'speed', {}).get('inference', 0) + 
                                getattr(result, 'speed', {}).get('postprocess', 0)
            }
        }
        
        if result.boxes is not None:
            boxes = result.boxes.data.cpu().numpy()
            formatted_result["metadata"]["num_detections"] = len(boxes)
            
            for i, box in enumerate(boxes):
                x1, y1, x2, y2, conf, cls = box
                detection = {
                    "id": i,
                    "class_id": int(cls),
                    "class_name": result.names[int(cls)],
                    "confidence": float(conf),
                    "bbox": {
                        "x1": float(x1),
                        "y1": float(y1),
                        "x2": float(x2),
                        "y2": float(y2),
                        "width": float(x2 - x1),
                        "height": float(y2 - y1)
                    }
                }
                formatted_result["detections"].append(detection)
        
        if result.masks is not None:
            masks_data = result.masks.data.cpu().numpy()
            for i, mask in enumerate(masks_data):
                # Convert mask to list for JSON serialization
                mask_list = mask.astype(bool).tolist()
                formatted_result["masks"].append({
                    "id": i,
                    "shape": list(mask.shape),
                    "data": mask_list
                })
        
        return formatted_result
    
    async def process_video_frame(
        self,
        frame: np.ndarray,
        model_name: str = None,
        confidence: float = 0.25,
        iou_threshold: float = 0.45
    ) -> Dict:
        """Process single video frame for real-time streaming"""
        return await self.predict_segmentation(
            frame, model_name, confidence, iou_threshold
        )
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported models"""
        return self.supported_models.copy()
    
    def get_default_model(self) -> str:
        """Get default model name"""
        return self.default_model


# Global service instance
mainCam_recognition_service = MainCamRecognitionService()
