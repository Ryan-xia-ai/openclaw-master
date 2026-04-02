"""
Document processing pipeline for Personal Knowledge Hub.
Handles file ingestion, preprocessing, and metadata extraction.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from src.core.database import KnowledgeHubDatabase
from src.core.embeddings import EmbeddingManager
from src.ingestion.chunker import TextChunker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes documents for ingestion into the knowledge hub."""
    
    def __init__(
        self, 
        database: KnowledgeHubDatabase, 
        embedding_manager: EmbeddingManager,
        config_path: str = "config/settings.yaml"
    ):
        """Initialize the document processor."""
        self.database = database
        self.embedding_manager = embedding_manager
        self.chunker = TextChunker(config_path)
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def process_file(
        self, 
        file_path: str, 
        collection_name: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process a single file and add it to the knowledge base.
        
        Args:
            file_path: Path to the file to process
            collection_name: Name of the collection to add to
            metadata: Additional metadata to associate with the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Read file content based on extension
            if file_ext == ".txt" or file_ext == ".md":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif file_ext == ".pdf":
                from src.ingestion.sources.pdf_handler import PDFHandler
                content = PDFHandler().extract_text(file_path)
            elif file_ext == ".docx":
                from src.ingestion.sources.file_handler import DOCXHandler
                content = DOCXHandler().extract_text(file_path)
            elif file_ext == ".html":
                from src.ingestion.sources.web_handler import HTMLHandler
                content = HTMLHandler().extract_text(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return False
            
            # Create default metadata if not provided
            if metadata is None:
                metadata = {}
            
            # Add file-specific metadata
            file_stat = os.stat(file_path)
            metadata.update({
                "source": "file",
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_extension": file_ext,
                "file_size": file_stat.st_size,
                "created_at": file_stat.st_ctime,
                "modified_at": file_stat.st_mtime,
                "document_id": self._generate_document_id(file_path, content)
            })
            
            # Process the content
            return self.process_content(content, collection_name, metadata)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return False
    
    def process_content(
        self, 
        content: str, 
        collection_name: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process raw content and add it to the knowledge base.
        
        Args:
            content: Raw text content to process
            collection_name: Name of the collection to add to
            metadata: Metadata to associate with the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Chunk the content
            chunks = self.chunker.chunk_text(content)
            
            # Generate embeddings for chunks
            embeddings = self.embedding_manager.embed_texts(chunks)
            
            # Create metadata for each chunk
            chunk_metadatas = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_size": len(chunk),
                    "total_chunks": len(chunks)
                })
                chunk_metadatas.append(chunk_metadata)
            
            # Generate IDs for chunks
            base_id = metadata.get("document_id", self._generate_document_id("content", content))
            chunk_ids = [f"{base_id}_chunk_{i}" for i in range(len(chunks))]
            
            # Add to database
            self.database.add_documents(
                collection_name=collection_name,
                documents=chunks,
                embeddings=embeddings,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )
            
            logger.info(f"Successfully processed content with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error processing content: {str(e)}")
            return False
    
    def _generate_document_id(self, source: str, content: str) -> str:
        """Generate a unique document ID based on source and content."""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        return f"{source}_{content_hash[:16]}"
    
    def process_directory(
        self, 
        directory_path: str, 
        collection_name: str = "default",
        recursive: bool = True
    ) -> Dict[str, int]:
        """
        Process all supported files in a directory.
        
        Args:
            directory_path: Path to the directory to process
            collection_name: Name of the collection to add to
            recursive: Whether to process subdirectories recursively
            
        Returns:
            Dictionary with counts of processed files by extension
        """
        supported_extensions = set(self.config["ingestion"]["supported_extensions"])
        file_counts = {}
        processed_count = 0
        
        path = Path(directory_path)
        if not path.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return file_counts
        
        # Get all files based on recursive setting
        if recursive:
            files = path.rglob("*")
        else:
            files = path.glob("*")
        
        for file_path in files:
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                if file_ext in supported_extensions:
                    if self.process_file(str(file_path), collection_name):
                        file_counts[file_ext] = file_counts.get(file_ext, 0) + 1
                        processed_count += 1
                    else:
                        logger.warning(f"Failed to process file: {file_path}")
        
        logger.info(f"Processed {processed_count} files from directory: {directory_path}")
        return file_counts