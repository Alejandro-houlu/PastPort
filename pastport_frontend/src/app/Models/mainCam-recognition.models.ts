export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  width: number;
  height: number;
}

export interface Detection {
  id: number;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
}

export interface MaskData {
  id: number;
  shape: number[];
  data: boolean[][];
}

export interface ImageShape {
  height: number;
  width: number;
  channels: number;
}

export interface RecognitionMetadata {
  num_detections: number;
  processing_time: number;
}

export interface RecognitionResult {
  image_shape: ImageShape;
  detections: Detection[];
  masks: MaskData[];
  metadata: RecognitionMetadata;
}

export interface PredictionResponse {
  success: boolean;
  data?: RecognitionResult;
  error?: string;
}

export interface RecognitionConfig {
  model_name: string;
  confidence: number;
  iou_threshold: number;
}

export interface WebSocketMessage {
  type: 'config' | 'frame' | 'ping';
  config?: RecognitionConfig;
  frame_data?: string;
  frame_id?: number;
  timestamp?: number;
}

export interface WebSocketResponse {
  type: 'config_updated' | 'recognition_result' | 'pong' | 'error';
  config?: RecognitionConfig;
  result?: RecognitionResult;
  frame_id?: number;
  timestamp?: number;
  message?: string;
}

export interface CaptureRequest {
  image_data: string;
  model_name?: string;
  confidence?: number;
  iou_threshold?: number;
}
