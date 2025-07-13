import os
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field
from .file_reading_tool import read_file_tool, FileContentOutput
from .image_reading_tool import read_image_tool, ImageContentOutput


class DocumentContentOutput(BaseModel):
    """Output model for document content processing."""
    file_path: str = Field(..., description="The path of the processed document.")
    file_type: str = Field(..., description="Type of the document (text, csv, pdf, docx, image).")
    content: Union[str, List[Dict[str, Any]]] = Field(..., description="The main content of the document.")
    extracted_text: str = Field("", description="Text extracted from the document (especially for images).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata information.")
    base64_content: Optional[str] = Field(None, description="Base64 encoded content for LLM processing (images only).")
    success: bool = Field(True, description="Whether the document was processed successfully.")
    error_message: str = Field("", description="Error message if processing failed.")


def process_document_tool(file_path: str, extract_text_from_images: bool = True) -> DocumentContentOutput:
    """
    Universal document processing tool that handles various file types including:
    - Text files (CSV, PDF, DOCX)
    - Image files (JPG, JPEG, PNG, GIF, BMP)
    
    Args:
        file_path: Path to the document file
        extract_text_from_images: Whether to extract text from images using OCR
        
    Returns:
        DocumentContentOutput containing processed content and metadata
    """
    
    if not os.path.exists(file_path):
        return DocumentContentOutput(
            file_path=file_path,
            file_type="unknown",
            content="",
            extracted_text="",
            base64_content=None,
            success=False,
            error_message="Document file not found."
        )
    
    try:
        # Get file extension
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()
        
        # Define supported file types
        text_files = ['.csv', '.pdf', '.docx', '.txt']
        image_files = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        
        if file_extension in text_files:
            # Process text-based documents
            result = read_file_tool(file_path)
            
            return DocumentContentOutput(
                file_path=file_path,
                file_type="text",
                content=result.content,
                extracted_text=str(result.content) if isinstance(result.content, str) else "",
                metadata={"file_extension": file_extension},
                base64_content=None,
                success=result.success,
                error_message=result.error_message
            )
            
        elif file_extension in image_files:
            # Process image files
            result = read_image_tool(file_path, extract_text=extract_text_from_images, include_base64=True)
            
            return DocumentContentOutput(
                file_path=file_path,
                file_type="image",
                content=result.extracted_text,
                extracted_text=result.extracted_text,
                metadata=result.image_info,
                base64_content=result.base64_content,
                success=result.success,
                error_message=result.error_message
            )
            
        else:
            return DocumentContentOutput(
                file_path=file_path,
                file_type="unsupported",
                content="",
                extracted_text="",
                base64_content=None,
                success=False,
                error_message=f"Unsupported file type: {file_extension}. Supported types: {text_files + image_files}"
            )
            
    except Exception as e:
        return DocumentContentOutput(
            file_path=file_path,
            file_type="error",
            content="",
            extracted_text="",
            base64_content=None,
            success=False,
            error_message=f"Error processing document: {str(e)}"
        )


def create_document_processing_tool(file_path: str, extract_text_from_images: bool = True):
    """
    Create a document processing tool function with pre-configured parameters.
    
    Args:
        file_path: Path to the document file
        extract_text_from_images: Whether to extract text from images using OCR
        
    Returns:
        A function that processes the specified document
    """
    
    def configured_document_processing_tool() -> DocumentContentOutput:
        return process_document_tool(file_path, extract_text_from_images)
    
    return configured_document_processing_tool


def extract_content_summary(document_content: DocumentContentOutput) -> str:
    """
    Extract a summary of document content for use in prompts.
    
    Args:
        document_content: The processed document content
        
    Returns:
        A formatted string summary of the document content
    """
    if not document_content.success:
        return f"❌ Lỗi xử lý tài liệu: {document_content.error_message}"
    
    summary_lines = [
        f"📄 **Tài liệu:** {os.path.basename(document_content.file_path)}",
        f"📝 **Loại:** {document_content.file_type.upper()}"
    ]
    
    # Add metadata information
    if document_content.metadata:
        if document_content.file_type == "image":
            meta = document_content.metadata
            summary_lines.append(f"🖼️ **Thông tin ảnh:** {meta.get('width', 'N/A')}x{meta.get('height', 'N/A')}, {meta.get('format', 'N/A')}")
        else:
            summary_lines.append(f"ℹ️ **Metadata:** {document_content.metadata}")
    
    # Add content preview
    if document_content.extracted_text:
        text_preview = document_content.extracted_text[:500] + "..." if len(document_content.extracted_text) > 500 else document_content.extracted_text
        summary_lines.append(f"📋 **Nội dung:**\n{text_preview}")
    elif isinstance(document_content.content, list):
        summary_lines.append(f"📊 **Dữ liệu:** {len(document_content.content)} dòng")
        if len(document_content.content) > 0:
            summary_lines.append(f"📋 **Cột:** {list(document_content.content[0].keys())}")
    elif isinstance(document_content.content, str):
        text_preview = document_content.content[:500] + "..." if len(document_content.content) > 500 else document_content.content
        summary_lines.append(f"📋 **Nội dung:**\n{text_preview}")
    
    return "\n".join(summary_lines)
