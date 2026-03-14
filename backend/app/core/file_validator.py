"""
File Upload Validation Service
"""
import os
import hashlib
import logging
from typing import List, Optional, Tuple
from fastapi import UploadFile
import io

# Try to import magic, fall back to basic detection if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

# Try to import PIL, fall back to basic validation if not available
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class FileValidationResult:
    """Result of file validation"""
    def __init__(
        self, 
        is_valid: bool, 
        errors: List[str] = None, 
        file_info: dict = None
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.file_info = file_info or {}


class FileValidator:
    """Comprehensive file upload validation"""
    
    # Allowed file types and their MIME types
    ALLOWED_IMAGE_TYPES = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'image/webp': ['.webp']
    }
    
    ALLOWED_DOCUMENT_TYPES = {
        'application/pdf': ['.pdf'],
        'text/plain': ['.txt'],
        'application/msword': ['.doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    }
    
    # File size limits (in bytes)
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Image dimension limits
    MAX_IMAGE_WIDTH = 4096
    MAX_IMAGE_HEIGHT = 4096
    MIN_IMAGE_WIDTH = 50
    MIN_IMAGE_HEIGHT = 50
    
    # Malicious file signatures (magic bytes)
    MALICIOUS_SIGNATURES = [
        b'\x4D\x5A',  # PE executable
        b'\x7F\x45\x4C\x46',  # ELF executable
        b'\xCA\xFE\xBA\xBE',  # Java class file
        b'\xFE\xED\xFA\xCE',  # Mach-O executable
        b'\xFE\xED\xFA\xCF',  # Mach-O executable (64-bit)
    ]
    
    @classmethod
    async def validate_upload_file(
        cls, 
        file: UploadFile, 
        allowed_types: str = "image",
        max_size: Optional[int] = None
    ) -> FileValidationResult:
        """
        Validate uploaded file
        
        Args:
            file: FastAPI UploadFile object
            allowed_types: "image", "document", or "any"
            max_size: Maximum file size in bytes
        """
        errors = []
        file_info = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': 0
        }
        
        try:
            # Read file content
            content = await file.read()
            file_size = len(content)
            file_info['size'] = file_size
            
            # Reset file pointer
            await file.seek(0)
            
            # Basic validations
            if not file.filename:
                errors.append("Filename is required")
                return FileValidationResult(False, errors, file_info)
            
            # File size validation
            max_allowed_size = max_size or (
                cls.MAX_IMAGE_SIZE if allowed_types == "image" else cls.MAX_DOCUMENT_SIZE
            )
            
            if file_size > max_allowed_size:
                errors.append(f"File size ({file_size} bytes) exceeds maximum allowed size ({max_allowed_size} bytes)")
            
            if file_size == 0:
                errors.append("File is empty")
            
            # File type validation
            file_extension = os.path.splitext(file.filename)[1].lower()
            detected_mime = cls._detect_mime_type(content)
            file_info['detected_mime'] = detected_mime
            file_info['extension'] = file_extension
            
            # Validate against allowed types
            allowed_mimes = {}
            if allowed_types == "image":
                allowed_mimes = cls.ALLOWED_IMAGE_TYPES
            elif allowed_types == "document":
                allowed_mimes = cls.ALLOWED_DOCUMENT_TYPES
            elif allowed_types == "any":
                allowed_mimes = {**cls.ALLOWED_IMAGE_TYPES, **cls.ALLOWED_DOCUMENT_TYPES}
            
            if detected_mime not in allowed_mimes:
                errors.append(f"File type '{detected_mime}' is not allowed")
            elif file_extension not in allowed_mimes[detected_mime]:
                errors.append(f"File extension '{file_extension}' does not match detected type '{detected_mime}'")
            
            # Malicious content detection
            if cls._contains_malicious_content(content):
                errors.append("File contains potentially malicious content")
                logger.warning(f"Malicious content detected in file: {file.filename}")
            
            # Image-specific validation
            if allowed_types == "image" and detected_mime in cls.ALLOWED_IMAGE_TYPES:
                image_errors = await cls._validate_image_content(content)
                errors.extend(image_errors)
                
                # Get image dimensions
                try:
                    image = Image.open(io.BytesIO(content))
                    file_info['width'] = image.width
                    file_info['height'] = image.height
                    file_info['format'] = image.format
                except Exception as e:
                    errors.append(f"Invalid image file: {str(e)}")
            
            # Generate file hash for deduplication
            file_info['hash'] = hashlib.sha256(content).hexdigest()
            
        except Exception as e:
            logger.error(f"Error validating file {file.filename}: {str(e)}")
            errors.append(f"File validation error: {str(e)}")
        
        return FileValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            file_info=file_info
        )
    
    @classmethod
    def _detect_mime_type(cls, content: bytes) -> str:
        """Detect MIME type from file content"""
        if MAGIC_AVAILABLE:
            try:
                # Use python-magic for accurate MIME detection
                mime = magic.from_buffer(content, mime=True)
                return mime
            except Exception:
                pass
        
        # Fallback to basic detection using file signatures
        if content.startswith(b'\xFF\xD8\xFF'):
            return 'image/jpeg'
        elif content.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
            return 'image/gif'
        elif content.startswith(b'RIFF') and b'WEBP' in content[:12]:
            return 'image/webp'
        elif content.startswith(b'%PDF'):
            return 'application/pdf'
        else:
            return 'application/octet-stream'
    
    @classmethod
    def _contains_malicious_content(cls, content: bytes) -> bool:
        """Check for malicious file signatures"""
        # Check first 1024 bytes for malicious signatures
        header = content[:1024]
        
        for signature in cls.MALICIOUS_SIGNATURES:
            if signature in header:
                return True
        
        # Check for embedded executables (basic check)
        if b'MZ' in header or b'ELF' in header:
            return True
        
        # Check for script injections in images
        if b'<script' in content.lower() or b'javascript:' in content.lower():
            return True
        
        return False
    
    @classmethod
    async def _validate_image_content(cls, content: bytes) -> List[str]:
        """Validate image-specific content"""
        errors = []
        
        if not PIL_AVAILABLE:
            # If PIL is not available, skip detailed image validation
            logger.warning("PIL not available, skipping detailed image validation")
            return errors
        
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(content))
            
            # Validate dimensions
            width, height = image.size
            
            if width > cls.MAX_IMAGE_WIDTH or height > cls.MAX_IMAGE_HEIGHT:
                errors.append(f"Image dimensions ({width}x{height}) exceed maximum allowed ({cls.MAX_IMAGE_WIDTH}x{cls.MAX_IMAGE_HEIGHT})")
            
            if width < cls.MIN_IMAGE_WIDTH or height < cls.MIN_IMAGE_HEIGHT:
                errors.append(f"Image dimensions ({width}x{height}) are below minimum required ({cls.MIN_IMAGE_WIDTH}x{cls.MIN_IMAGE_HEIGHT})")
            
            # Validate image format
            if image.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                errors.append(f"Unsupported image format: {image.format}")
            
            # Check for EXIF data that might contain malicious content
            if hasattr(image, '_getexif') and image._getexif():
                exif_data = image._getexif()
                if exif_data:
                    # Check for suspicious EXIF data
                    for tag, value in exif_data.items():
                        if isinstance(value, str) and any(
                            suspicious in value.lower() 
                            for suspicious in ['<script', 'javascript:', 'vbscript:']
                        ):
                            errors.append("Image contains suspicious EXIF data")
                            break
            
        except Exception as e:
            errors.append(f"Invalid image file: {str(e)}")
        
        return errors
    
    @classmethod
    def get_safe_filename(cls, filename: str) -> str:
        """Generate a safe filename"""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        safe_filename = ''.join(c if c in safe_chars else '_' for c in filename)
        
        # Ensure filename is not empty and has reasonable length
        if not safe_filename or safe_filename.startswith('.'):
            safe_filename = 'file_' + safe_filename
        
        if len(safe_filename) > 255:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:255-len(ext)] + ext
        
        return safe_filename
    
    @classmethod
    def calculate_file_hash(cls, content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()


# Convenience functions
async def validate_image_upload(file: UploadFile, max_size: int = None) -> FileValidationResult:
    """Validate image upload"""
    return await FileValidator.validate_upload_file(file, "image", max_size)


async def validate_document_upload(file: UploadFile, max_size: int = None) -> FileValidationResult:
    """Validate document upload"""
    return await FileValidator.validate_upload_file(file, "document", max_size)


def get_allowed_file_types() -> dict:
    """Get dictionary of allowed file types"""
    return {
        "images": list(FileValidator.ALLOWED_IMAGE_TYPES.keys()),
        "documents": list(FileValidator.ALLOWED_DOCUMENT_TYPES.keys())
    }