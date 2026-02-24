from abc import ABC, abstractmethod
from typing import Optional, Dict, Callable
import os
from app.core.logging import get_logger
from app.utils.file import detect_file_type
from app.core.config import settings

logger = get_logger(__name__)

class BaseProcessor(ABC):
    """Abstract base class for all document processors."""
    
    def __init__(self, session_id: str):

        self.session_id = session_id
        self.temp_folder = settings.temp_file_path
        self.db_path = os.path.join(self.temp_folder, f"{session_id}.db")
        self.logger = logger
    
    @abstractmethod
    def process(self, file_path: str, filename: str,delete_file: bool = True) -> Optional[str]:
        """
        Process the document and return the database path.
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            
        Returns:
            Path to the SQLite database or None if processing failed
        """
        pass
    
    def _ensure_temp_folder(self):
        """Create temp folder if it doesn't exist."""
        os.makedirs(self.temp_folder, exist_ok=True)
    
    def _cleanup_uploaded_file(self, file_path: str):
        """Delete the uploaded file after processing."""
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                self.logger.info("Deleted uploaded file: %s", file_path)
            except Exception as e:
                self.logger.warning("Failed to delete uploaded file %s: %s", file_path, e)
    


class PDFProcessor(BaseProcessor):
    """Processor for PDF files."""
    
    def process(self, file_path: str, filename: str,delete_file: bool = True) -> Optional[str]:
        """Process PDF file."""
        self.logger.info("Processing PDF file: %s | session_id=%s", filename, self.session_id)
        self._cleanup_uploaded_file(file_path)  
        return None


class WordProcessor(BaseProcessor):
    """Processor for Word documents."""
    
    def process(self, file_path: str, filename: str,delete_file: bool = True) -> Optional[str]:
        """Process Word document."""
        self.logger.info("Processing Word file: %s | session_id=%s", filename, self.session_id)
        # TODO: Implement Word processing
        self._cleanup_uploaded_file(file_path)
        return None


class TextProcessor(BaseProcessor):
    """Processor for text files."""
    
    def process(self, file_path: str, filename: str,delete_file: bool = True) -> Optional[str]:
        """Process text file."""
        self.logger.info("Processing text file: %s | session_id=%s", filename, self.session_id)
        # TODO: Implement text processing
        self._cleanup_uploaded_file(file_path)
        return None



class OtherProcessor(BaseProcessor):
    """Processor for unrecognized file types."""
    
    def process(self, file_path: str, filename: str,delete_file: bool = True) -> Optional[str]:
        """Process other file types."""
        self.logger.info("Processing other file: %s | session_id=%s", filename, self.session_id)
        # TODO: Implement generic processing
        self._cleanup_uploaded_file(file_path)
        return None



class DocumentIngestionService:
    """Main service class for document ingestion."""
    
    def __init__(self):
        self.logger = logger
        self._processor_map: Dict[str, type[BaseProcessor]] = {

            'pdf': PDFProcessor,
            'word': WordProcessor,
            'text': TextProcessor,
            'other': OtherProcessor,
        }
    
    def ingest_document(self, file_path: str, filename: str, session_id: str,delete_file: bool = True) -> Optional[str]:
        """
        Ingest a document by detecting its type and routing to appropriate processor.
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            session_id: Unique session identifier
            
        Returns:
            Path to the processed database or None if processing failed
        """
        self.logger.info("Processing %s", filename)
        
        # Detect file type
        file_type = detect_file_type(file_path)
        self.logger.info("Detected file type: %s", file_type)
        
        # Get appropriate processor class
        processor_class = self._processor_map.get(file_type, OtherProcessor)
        
        # Instantiate processor and process the file
        processor = processor_class(session_id)
        result = processor.process(file_path, filename,delete_file)
        
        return result

        """
        Register a custom processor for a file type.
        
        Args:
            file_type: The file type identifier
            processor_class: The processor class to handle this type
        
        Sample Usage 
        def custom_processor_usage():
            
            service = DocumentIngestionService()
            
            # Register custom processor
            service.register_processor('json', JSONProcessor)
            
            # Now JSON files will be processed with JSONProcessor
            db_path = service.ingest_document(
                file_path="/path/to/data.json",
                filename="data.json",
                session_id="user_session_123"
            )

        """
        if not issubclass(processor_class, BaseProcessor):
            raise ValueError("Processor must inherit from BaseProcessor")
        self._processor_map[file_type] = processor_class
        self.logger.info("Registered processor %s for file type '%s'", 
                        processor_class.__name__, file_type)