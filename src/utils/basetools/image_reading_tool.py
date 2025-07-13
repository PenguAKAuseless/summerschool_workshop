import base64
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from PIL import Image
import io
import pytesseract


class ImageContentOutput(BaseModel):
    """Output model for image content."""
    file_path: str = Field(..., description="The path of the read image file.")
    extracted_text: str = Field("", description="Text extracted from the image via OCR.")
    image_info: Dict[str, Any] = Field(default_factory=dict, description="Image metadata information.")
    base64_content: Optional[str] = Field(None, description="Base64 encoded image content for LLM processing.")
    success: bool = Field(True, description="Whether the image was processed successfully.")
    error_message: str = Field("", description="Error message if processing failed.")


def read_image_tool(file_path: str, extract_text: bool = True, include_base64: bool = True) -> ImageContentOutput:
    """
    Reads and processes an image file (JPG, PNG, GIF, BMP).
    
    Args:
        file_path: Path to the image file
        extract_text: Whether to extract text from image using OCR
        include_base64: Whether to include base64 encoded image for LLM processing
        
    Returns:
        ImageContentOutput containing extracted text, metadata, and optionally base64 content
    """
    
    if not os.path.exists(file_path):
        return ImageContentOutput(
            file_path=file_path,
            success=False,
            error_message="Image file not found."
        )
    
    try:
        # Open and process the image
        with Image.open(file_path) as img:
            # Get image metadata
            image_info = {
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height
            }
            
            # Extract text using OCR if requested
            extracted_text = ""
            if extract_text:
                try:
                    extracted_text = pytesseract.image_to_string(img, lang='vie+eng')
                    extracted_text = extracted_text.strip()
                except Exception as ocr_error:
                    extracted_text = f"OCR processing failed: {str(ocr_error)}"
            
            # Convert to base64 if requested
            base64_content = None
            if include_base64:
                try:
                    # Convert image to RGB if necessary for consistent processing
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Save to bytes buffer
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG')
                    image_bytes = buffer.getvalue()
                    
                    # Encode to base64
                    base64_content = base64.b64encode(image_bytes).decode('utf-8')
                except Exception as b64_error:
                    base64_content = f"Base64 encoding failed: {str(b64_error)}"
        
        return ImageContentOutput(
            file_path=file_path,
            extracted_text=extracted_text,
            image_info=image_info,
            base64_content=base64_content,
            success=True,
            error_message=""
        )
        
    except Exception as e:
        return ImageContentOutput(
            file_path=file_path,
            success=False,
            error_message=f"Error processing image: {str(e)}"
        )


def create_image_reading_tool(file_path: str, extract_text: bool = True, include_base64: bool = True):
    """
    Create an image reading tool function with pre-configured parameters.
    
    Args:
        file_path: Path to the image file
        extract_text: Whether to extract text from image using OCR
        include_base64: Whether to include base64 encoded image for LLM processing
        
    Returns:
        A function that reads and processes the specified image
    """
    
    def configured_image_reading_tool() -> ImageContentOutput:
        return read_image_tool(file_path, extract_text, include_base64)
    
    return configured_image_reading_tool
