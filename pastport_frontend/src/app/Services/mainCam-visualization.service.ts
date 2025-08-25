import { Injectable } from '@angular/core';
import { 
  RecognitionResult, 
  Detection, 
  BoundingBox 
} from '../Models/mainCam-recognition.models';

@Injectable({
  providedIn: 'root'
})
export class MainCamVisualizationService {

  constructor() {}

  /**
   * Draw recognition results on canvas overlay
   */
  drawRecognitionResults(
    canvas: HTMLCanvasElement, 
    results: RecognitionResult,
    options: VisualizationOptions = {}
  ): void {
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      console.error('Could not get canvas context');
      return;
    }

    // console.log(`🎨 Drawing recognition results on ${canvas.width}x${canvas.height} canvas`);
    // console.log(`📊 Image shape: ${results.image_shape.width}x${results.image_shape.height}`);
    // console.log(`🎯 Found ${results.detections.length} detections, ${results.masks.length} masks`);

    // Clear previous drawings
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Set default options
    const opts = {
      showBoxes: false, // Disable bounding boxes - only show masks and labels
      showLabels: true,
      showConfidence: true,
      showMasks: true, // Enable masks by default
      boxColor: '#ad64f1',
      labelColor: '#ffffff',
      labelBackgroundColor: '#ad64f1',
      lineWidth: 2,
      fontSize: 14,
      fontFamily: 'Arial, sans-serif',
      minConfidence: 0.3,
      onMaskClick: () => {}, // Default empty callback
      ...options
    };

    // Calculate CSS 'object-fit: cover' scaling for bounding boxes
    // This accounts for how the video is cropped and scaled in the display
    const cw = canvas.width;
    const ch = canvas.height;
    const vw = results.image_shape.width;
    const vh = results.image_shape.height;
    
    // Calculate uniform scale factor (same as TravelDex)
    const scale = Math.max(cw/vw, ch/vh);
    const sw = cw/scale;  // How many source pixels wide the container shows
    const sh = ch/scale;  // How many source pixels tall
    const sx = (vw - sw)/2;  // Cropped off left
    const sy = (vh - sh)/2;  // Cropped off top
    
    console.log(`📏 CSS Cover scaling: scale=${scale.toFixed(3)}, visible=${sw.toFixed(1)}x${sh.toFixed(1)}, offset=(${sx.toFixed(1)}, ${sy.toFixed(1)})`);

    // Draw masks FIRST (before boxes and labels) to prevent erasure
    if (results.masks && results.masks.length > 0 && opts.showMasks) {
      console.log(`🎭 Drawing ${results.masks.length} segmentation masks`);
      results.masks.forEach((mask, index) => {
        if (index < results.detections.length) {
          const detection = results.detections[index];
          if (detection.confidence >= opts.minConfidence) {
            this.drawMask(ctx, mask, canvas, opts, scale, sx, sy);
          }
        }
      });
    }

    // Draw detections AFTER masks (so they stay visible)
    if (results.detections && results.detections.length > 0) {
      results.detections.forEach(detection => {
        if (detection.confidence >= opts.minConfidence) {
          this.drawDetection(ctx, detection, canvas, opts, scale, sx, sy);
        }
      });
    }
  }

  /**
   * Draw a single detection (bounding box and label)
   */
  private drawDetection(
    ctx: CanvasRenderingContext2D,
    detection: Detection,
    canvas: HTMLCanvasElement,
    options: Required<VisualizationOptions>,
    scale: number,
    sx: number,
    sy: number
  ): void {
    const bbox = detection.bbox;
    
    // Apply CSS 'object-fit: cover' scaling with crop adjustment (TravelDx approach)
    // Transform both corner coordinates first, then calculate dimensions
    const x1_transformed = (bbox.x1 - sx) * scale;
    const y1_transformed = (bbox.y1 - sy) * scale;
    const x2_transformed = (bbox.x2 - sx) * scale;
    const y2_transformed = (bbox.y2 - sy) * scale;
    
    // Calculate final position and dimensions from transformed coordinates
    const x = x1_transformed;
    const y = y1_transformed;
    const width = x2_transformed - x1_transformed;
    const height = y2_transformed - y1_transformed;

    // console.log(`🎨 Drawing detection: ${detection.class_name} at (${x.toFixed(1)}, ${y.toFixed(1)}) size ${width.toFixed(1)}x${height.toFixed(1)}`);
    // console.log(`🔧 Transform: bbox(${bbox.x1}, ${bbox.y1}, ${bbox.x2}, ${bbox.y2}) -> canvas(${x.toFixed(1)}, ${y.toFixed(1)}, ${width.toFixed(1)}, ${height.toFixed(1)})`);

    // Skip any box entirely off-screen
    if (x + width < 0 || y + height < 0 || x > canvas.width || y > canvas.height) {
      console.log(`⏭️ Skipping off-screen detection: ${detection.class_name}`);
      return;
    }

    // Draw bounding box with dynamic line width
    if (options.showBoxes) {
      // Calculate dynamic line width based on canvas size
      const canvasSize = Math.min(canvas.width, canvas.height);
      const dynamicLineWidth = Math.max(2, Math.min(6, canvasSize / 150)); // Scales from 2px to 6px
      
      ctx.strokeStyle = options.boxColor;
      ctx.lineWidth = dynamicLineWidth;
      ctx.strokeRect(x, y, width, height);
      console.log(`📦 Drew bounding box for ${detection.class_name} with ${dynamicLineWidth}px line width`);
    }

    // Draw label
    if (options.showLabels) {
      const label = options.showConfidence 
        ? `${detection.class_name} (${(detection.confidence * 100).toFixed(1)}%)`
        : detection.class_name;

      // Pass the bottom of the bounding box (y + height) for label positioning
      this.drawLabel(ctx, label, x, y + height, options);
      console.log(`🏷️ Drew label: ${label}`);
    }
  }

  /**
   * Draw label with background below the bounding box - fully responsive
   */
  private drawLabel(
    ctx: CanvasRenderingContext2D,
    text: string,
    x: number,
    y: number,
    options: Required<VisualizationOptions>
  ): void {
    // Calculate dynamic font size based on canvas resolution
    const canvasSize = Math.min(ctx.canvas.width, ctx.canvas.height);
    const dynamicFontSize = Math.max(12, Math.min(24, canvasSize / 30)); // Scales from 12px to 24px
    
    // Calculate dynamic padding based on canvas size
    const dynamicPadding = Math.max(4, Math.min(12, canvasSize / 80)); // Scales from 4px to 12px
    
    // Calculate dynamic line width based on canvas size
    const dynamicLineWidth = Math.max(1, Math.min(3, canvasSize / 200)); // Scales from 1px to 3px
    
    ctx.font = `bold ${dynamicFontSize}px ${options.fontFamily}`;
    const textMetrics = ctx.measureText(text);
    const textWidth = textMetrics.width;
    const textHeight = dynamicFontSize;

    let labelX = x;
    let labelY = y + dynamicPadding; // Position below the bounding box
    const labelWidth = textWidth + dynamicPadding * 2;
    const labelHeight = textHeight + dynamicPadding * 2;

    // Ensure label stays within canvas bounds - responsive to any resolution
    if (labelX + labelWidth > ctx.canvas.width) {
      labelX = ctx.canvas.width - labelWidth - dynamicPadding;
    }
    if (labelY + labelHeight > ctx.canvas.height) {
      labelY = y - labelHeight - dynamicPadding; // Move above if no space below
    }
    if (labelX < 0) labelX = dynamicPadding;
    if (labelY < 0) labelY = dynamicPadding;

    console.log(`🏷️ Drawing responsive label "${text}" at (${labelX.toFixed(1)}, ${labelY.toFixed(1)}) - Font: ${dynamicFontSize}px, Padding: ${dynamicPadding}px`);

    // Draw label background with stronger visibility
    ctx.fillStyle = options.labelBackgroundColor;
    ctx.fillRect(labelX, labelY, labelWidth, labelHeight);

    // Add a white border for better visibility on any background
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = dynamicLineWidth;
    ctx.strokeRect(labelX, labelY, labelWidth, labelHeight);

    // Draw label text with proper vertical centering
    ctx.fillStyle = options.labelColor;
    ctx.fillText(text, labelX + dynamicPadding, labelY + textHeight + (dynamicPadding / 2));
    
    console.log(`✅ Responsive label "${text}" drawn successfully - Canvas: ${ctx.canvas.width}x${ctx.canvas.height}`);
  }

  /**
   * Draw segmentation mask using Canvas 2D API (doesn't erase other drawings)
   */
  private drawMask(
    ctx: CanvasRenderingContext2D,
    mask: any,
    canvas: HTMLCanvasElement,
    options: Required<VisualizationOptions>,
    bboxScale: number,
    bboxSx: number,
    bboxSy: number
  ): void {
    console.log(`🎭 Drawing mask with shape: ${mask.shape}`);
    
    if (mask.data && Array.isArray(mask.data)) {
      const maskHeight = mask.shape[0]; // 384
      const maskWidth = mask.shape[1];  // 640
      
      console.log(`🎭 Mask dimensions: ${maskWidth}x${maskHeight}, Canvas: ${canvas.width}x${canvas.height}`);
      
      // Calculate CSS 'object-fit: cover' scaling for masks
      // Masks have their own coordinate system, so we need separate calculations
      const cw = canvas.width;
      const ch = canvas.height;
      const mw = maskWidth;
      const mh = maskHeight;
      
      // Calculate uniform scale factor for mask coordinates
      const maskScale = Math.max(cw/mw, ch/mh);
      const msw = cw/maskScale;  // How many mask pixels wide the container shows
      const msh = ch/maskScale;  // How many mask pixels tall
      const msx = (mw - msw)/2;  // Cropped off left in mask space
      const msy = (mh - msh)/2;  // Cropped off top in mask space
      
      console.log(`🎭 Mask CSS Cover scaling: scale=${maskScale.toFixed(3)}, visible=${msw.toFixed(1)}x${msh.toFixed(1)}, offset=(${msx.toFixed(1)}, ${msy.toFixed(1)})`);
      
      // Use Canvas 2D API instead of putImageData to avoid erasing other drawings
      ctx.fillStyle = 'rgba(173, 100, 241, 0.4)'; // Semi-transparent purple
      
      let pixelCount = 0;
      
      // Calculate pixel size for efficient rendering
      const pixelSize = Math.max(1, Math.min(maskScale, 3));
      
      for (let maskY = 0; maskY < maskHeight; maskY++) {
        for (let maskX = 0; maskX < maskWidth; maskX++) {
          if (mask.data[maskY] && mask.data[maskY][maskX]) {
            // Apply CSS 'object-fit: cover' scaling with crop adjustment for masks
            const canvasX = (maskX - msx) * maskScale;
            const canvasY = (maskY - msy) * maskScale;
            
            // Only draw if within canvas bounds
            if (canvasX >= 0 && canvasY >= 0 && canvasX < canvas.width && canvasY < canvas.height) {
              // Draw a small rectangle for this mask pixel
              ctx.fillRect(Math.floor(canvasX), Math.floor(canvasY), pixelSize, pixelSize);
              pixelCount++;
            }
          }
        }
      }
      
      console.log(`✅ Drew segmentation mask overlay using CSS Cover scaling - ${pixelCount} mask pixels processed`);
    } else {
      console.log('⚠️ Mask data format not supported for rendering');
    }
  }

  /**
   * Create overlay canvas element
   */
  createOverlayCanvas(video: HTMLVideoElement): HTMLCanvasElement {
    const canvas = document.createElement('canvas');
    
    // Use display dimensions instead of video dimensions (TravelDx approach)
    canvas.width = video.clientWidth;
    canvas.height = video.clientHeight;
    
    // Style the canvas to overlay on video
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '10';

    return canvas;
  }

  /**
   * Update overlay canvas size to match video display (TravelDx approach)
   */
  updateCanvasSize(canvas: HTMLCanvasElement, video: HTMLVideoElement): void {
    // Use CSS-computed (client) pixel size of the video element
    // This matches TravelDx's approach for proper CSS 'object-fit: cover' handling
    const cw = video.clientWidth;
    const ch = video.clientHeight;
    
    console.log(`📐 Updating canvas size - Video: ${video.videoWidth}x${video.videoHeight}, Display: ${cw}x${ch}`);
    
    // Make the internal drawing surface match the display size exactly
    canvas.width = cw;
    canvas.height = ch;
    
    // CSS styling should match the display dimensions
    canvas.style.width = cw + 'px';
    canvas.style.height = ch + 'px';
    
    console.log(`📐 Canvas dimensions set to display size - Internal: ${canvas.width}x${canvas.height}, CSS: ${canvas.style.width}x${canvas.style.height}`);
  }

  /**
   * Clear overlay canvas
   */
  clearOverlay(canvas: HTMLCanvasElement): void {
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  /**
   * Get color for detection class
   */
  getClassColor(classId: number): string {
    const colors = [
      '#ad64f1', // Primary purple
      '#4788ff', // Secondary blue
      '#ff6b6b', // Red
      '#4ecdc4', // Teal
      '#45b7d1', // Light blue
      '#96ceb4', // Green
      '#feca57', // Yellow
      '#ff9ff3', // Pink
      '#54a0ff', // Blue
      '#5f27cd'  // Dark purple
    ];
    
    return colors[classId % colors.length];
  }

  /**
   * Calculate optimal font size based on canvas size
   */
  calculateFontSize(canvas: HTMLCanvasElement): number {
    const baseSize = Math.min(canvas.width, canvas.height);
    return Math.max(12, Math.min(20, baseSize / 40));
  }

  /**
   * Check if point is inside bounding box
   */
  isPointInBoundingBox(x: number, y: number, bbox: BoundingBox): boolean {
    return x >= bbox.x1 && x <= bbox.x2 && y >= bbox.y1 && y <= bbox.y2;
  }

  /**
   * Get detection at point (for click handling)
   */
  getDetectionAtPoint(
    x: number, 
    y: number, 
    results: RecognitionResult,
    canvas: HTMLCanvasElement
  ): Detection | null {
    console.log('🔍 DETECTION DEBUG: getDetectionAtPoint called');
    console.log('🔍 DETECTION DEBUG: Click point:', x, y);
    console.log('🔍 DETECTION DEBUG: Canvas size:', canvas.width, canvas.height);
    console.log('🔍 DETECTION DEBUG: Image shape:', results.image_shape);
    
    if (!results.detections) {
      console.log('🔍 DETECTION DEBUG: No detections available');
      return null;
    }

    // Use the same CSS 'object-fit: cover' scaling logic as drawing
    const cw = canvas.width;
    const ch = canvas.height;
    const vw = results.image_shape.width;
    const vh = results.image_shape.height;
    
    const scale = Math.max(cw/vw, ch/vh);
    const sw = cw/scale;
    const sh = ch/scale;
    const sx = (vw - sw)/2;
    const sy = (vh - sh)/2;

    console.log('🔍 DETECTION DEBUG: Scaling info:');
    console.log('  - scale:', scale);
    console.log('  - visible area:', sw, 'x', sh);
    console.log('  - offset:', sx, sy);

    // Find detection at point using transformed coordinates
    let bestDetection: Detection | null = null;
    let bestConfidence = 0;

    for (let i = 0; i < results.detections.length; i++) {
      const detection = results.detections[i];
      const bbox = detection.bbox;
      
      // Transform bounding box coordinates to canvas space
      const x1_transformed = (bbox.x1 - sx) * scale;
      const y1_transformed = (bbox.y1 - sy) * scale;
      const x2_transformed = (bbox.x2 - sx) * scale;
      const y2_transformed = (bbox.y2 - sy) * scale;
      
      console.log(`🔍 DETECTION DEBUG: Detection ${i} (${detection.class_name}):`);
      console.log('  - Original bbox:', bbox);
      console.log('  - Transformed bbox:', {
        x1: x1_transformed.toFixed(1),
        y1: y1_transformed.toFixed(1),
        x2: x2_transformed.toFixed(1),
        y2: y2_transformed.toFixed(1)
      });
      
      // Check if click point is within transformed bounding box
      const isInside = x >= x1_transformed && x <= x2_transformed && 
                      y >= y1_transformed && y <= y2_transformed;
      
      console.log('  - Click inside?', isInside);
      console.log('  - X check:', x, '>=', x1_transformed.toFixed(1), '&&', x, '<=', x2_transformed.toFixed(1), '=', (x >= x1_transformed && x <= x2_transformed));
      console.log('  - Y check:', y, '>=', y1_transformed.toFixed(1), '&&', y, '<=', y2_transformed.toFixed(1), '=', (y >= y1_transformed && y <= y2_transformed));
      
      if (isInside) {
        console.log('  - ✅ Click is inside this detection!');
        if (detection.confidence > bestConfidence) {
          bestDetection = detection;
          bestConfidence = detection.confidence;
          console.log('  - 🏆 New best detection:', detection.class_name, 'confidence:', detection.confidence);
        }
      }
    }

    console.log('🔍 DETECTION DEBUG: Final result:', bestDetection ? bestDetection.class_name : 'null');
    return bestDetection;
  }
}

export interface VisualizationOptions {
  showBoxes?: boolean;
  showLabels?: boolean;
  showConfidence?: boolean;
  showMasks?: boolean;
  boxColor?: string;
  labelColor?: string;
  labelBackgroundColor?: string;
  lineWidth?: number;
  fontSize?: number;
  fontFamily?: string;
  minConfidence?: number;
  onMaskClick?: (detection: Detection) => void;
}
