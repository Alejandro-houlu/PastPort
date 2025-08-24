from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Union
import base64
import json
import aiohttp
import numpy as np
from app.services.mainCam_service import mainCam_recognition_service

router = APIRouter()


class ImagePredictionRequest(BaseModel):
    image_data: str  # base64 encoded image
    model_name: Optional[str] = "yolo11n-seg-custom-v7.pt"
    confidence: Optional[float] = 0.25
    iou_threshold: Optional[float] = 0.45


class PredictionResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


@router.get("/health")
async def health_check():
    """Health check endpoint for mainCam recognition"""
    print("🏥 MainCam API: Health check requested")
    return {"status": "healthy", "service": "MainCam Recognition API"}


@router.get("/models")
async def get_supported_models():
    """Get list of supported YOLO models"""
    print("📋 MainCam API: Supported models requested")
    models_info = {
        "supported_models": mainCam_recognition_service.get_supported_models(),
        "default_model": mainCam_recognition_service.get_default_model()
    }
    print(f"📋 MainCam API: Returning {len(models_info['supported_models'])} supported models")
    return models_info


@router.post("/predict/upload", response_model=PredictionResponse)
async def predict_from_upload(
    file: UploadFile = File(...),
    model_name: Optional[str] = Form("yolo11n-seg-custom-v7.pt"),
    confidence: Optional[float] = Form(0.25),
    iou_threshold: Optional[float] = Form(0.45)
):
    """Predict segmentation from uploaded image file"""
    print(f"📤 MainCam API: Upload prediction request - file: {file.filename}, model: {model_name}")
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            print(f"❌ MainCam API: Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")
        
        print(f"📁 MainCam API: Processing {file.content_type} file ({file.size} bytes)")
        
        # Read file content
        file_content = await file.read()
        print(f"📥 MainCam API: File content read ({len(file_content)} bytes)")
        
        # Process prediction
        result = await mainCam_recognition_service.predict_segmentation(
            file_content, model_name, confidence, iou_threshold
        )
        
        detections = result.get("metadata", {}).get("num_detections", 0)
        print(f"✅ MainCam API: Upload prediction complete - {detections} detections")
        return PredictionResponse(success=True, data=result)
        
    except Exception as e:
        print(f"💥 MainCam API: Upload prediction error: {str(e)}")
        return PredictionResponse(success=False, error=str(e))


@router.post("/predict/base64", response_model=PredictionResponse)
async def predict_from_base64(request: ImagePredictionRequest):
    """Predict segmentation from base64 encoded image"""
    print(f"📊 MainCam API: Base64 prediction request - model: {request.model_name}, conf: {request.confidence}")
    try:
        data_length = len(request.image_data)
        print(f"📥 MainCam API: Processing base64 data ({data_length} chars)")
        
        result = await mainCam_recognition_service.predict_segmentation(
            request.image_data,
            request.model_name,
            request.confidence,
            request.iou_threshold
        )
        
        detections = result.get("metadata", {}).get("num_detections", 0)
        print(f"✅ MainCam API: Base64 prediction complete - {detections} detections")
        return PredictionResponse(success=True, data=result)
        
    except Exception as e:
        print(f"💥 MainCam API: Base64 prediction error: {str(e)}")
        return PredictionResponse(success=False, error=str(e))


@router.post("/predict/url")
async def predict_from_url(
    image_url: str,
    model_name: Optional[str] = "yolo11n-seg-custom-v7.pt",
    confidence: Optional[float] = 0.25,
    iou_threshold: Optional[float] = 0.45
):
    """Predict segmentation from image URL"""
    print(f"🌐 MainCam API: URL prediction request - URL: {image_url}, model: {model_name}")
    try:
        print(f"📡 MainCam API: Fetching image from URL: {image_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    print(f"❌ MainCam API: Failed to fetch image - HTTP {response.status}")
                    raise HTTPException(status_code=400, detail="Failed to fetch image from URL")
                
                image_data = await response.read()
                print(f"📥 MainCam API: Downloaded {len(image_data)} bytes from URL")
        
        result = await mainCam_recognition_service.predict_segmentation(
            image_data, model_name, confidence, iou_threshold
        )
        
        detections = result.get("metadata", {}).get("num_detections", 0)
        print(f"✅ MainCam API: URL prediction complete - {detections} detections")
        return PredictionResponse(success=True, data=result)
        
    except Exception as e:
        print(f"💥 MainCam API: URL prediction error: {str(e)}")
        return PredictionResponse(success=False, error=str(e))


@router.post("/capture", response_model=PredictionResponse)
async def capture_and_predict(request: ImagePredictionRequest):
    """Process captured image from camera (same as base64 but with different endpoint name for clarity)"""
    print(f"📸 MainCam API: Capture prediction request - model: {request.model_name}, conf: {request.confidence}")
    try:
        data_length = len(request.image_data)
        print(f"📥 MainCam API: Processing captured frame ({data_length} chars)")
        
        result = await mainCam_recognition_service.predict_segmentation(
            request.image_data,
            request.model_name,
            request.confidence,
            request.iou_threshold
        )
        
        detections = result.get("metadata", {}).get("num_detections", 0)
        processing_time = result.get("metadata", {}).get("processing_time", 0)
        print(f"✅ MainCam API: Capture prediction complete - {detections} detections in {processing_time:.1f}ms")
        return PredictionResponse(success=True, data=result)
        
    except Exception as e:
        print(f"💥 MainCam API: Capture prediction error: {str(e)}")
        return PredictionResponse(success=False, error=str(e))
