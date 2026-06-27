import cv2
import numpy as np
from PIL import Image

def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """
    Applies grayscale, denoising, and adaptive thresholding
    to prepare an image for Tesseract OCR.
    """
    # Convert PIL Image to OpenCV format
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # 1. Grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # 2. Denoise (Non-local Means Denoising)
    denoised = cv2.fastNlMeansDenoising(gray, h=10, searchWindowSize=21, templateWindowSize=7)
    
    # 3. Adaptive Thresholding
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # Return as PIL Image
    return Image.fromarray(thresh)
