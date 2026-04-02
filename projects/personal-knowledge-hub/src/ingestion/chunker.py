"""
Text chunking strategies for Personal Knowledge Hub.
Handles splitting documents into appropriately sized chunks.
"""

import logging
from typing import List, Optional
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextChunker:
    """Handles text chunking with configurable strategies."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the chunker with configuration."""
        self.config = self._load_config(config_path)
        self.chunk_size = self.config["ingestion"]["chunk_size"]
        self.chunk_overlap = self.config["ingestion"]["chunk_overlap"]
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def chunk_text(self, text: str, chunk_size: Optional[int] = None, 
                   chunk_overlap: Optional[int] = None) -> List[str]:
        """
        Split text into chunks of specified size with overlap.
        
        Args:
            text: Input text to chunk
            chunk_size: Override default chunk size (optional)
            chunk_overlap: Override default chunk overlap (optional)
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        actual_chunk_size = chunk_size if chunk_size is not None else self.chunk_size
        actual_chunk_overlap = chunk_overlap if chunk_overlap is not None else self.chunk_overlap
        
        if actual_chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        
        if actual_chunk_overlap >= actual_chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        
        # Simple character-based chunking
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + actual_chunk_size, text_length)
            chunk = text[start:end]
            
            # Try to break at sentence boundaries if possible
            if end < text_length:
                # Look for sentence endings in the last part of the chunk
                boundary_chars = '.!?\n'
                best_break = -1
                for i in range(len(chunk) - 1, max(0, len(chunk) - 100), -1):
                    if chunk[i] in boundary_chars:
                        best_break = i + 1
                        break
                
                if best_break > 0 and best_break < len(chunk):
                    chunk = chunk[:best_break]
                    end = start + best_break
            
            chunks.append(chunk)
            start = end - actual_chunk_overlap if actual_chunk_overlap > 0 else end
        
        # Remove empty chunks
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        logger.info(f"Chunked text into {len(chunks)} chunks")
        return chunks
    
    def chunk_by_paragraphs(self, text: str, max_chunk_size: Optional[int] = None) -> List[str]:
        """
        Chunk text by paragraphs, combining small paragraphs if needed.
        
        Args:
            text: Input text to chunk
            max_chunk_size: Maximum size for combined chunks (defaults to config)
            
        Returns:
            List of paragraph-based chunks
        """
        if not text or not text.strip():
            return []
        
        actual_max_size = max_chunk_size if max_chunk_size is not None else self.chunk_size
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if not paragraphs:
            # Fallback to character chunking
            return self.chunk_text(text)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= actual_max_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(paragraph) > actual_max_size:
                    # Paragraph is too long, fall back to character chunking
                    para_chunks = self.chunk_text(paragraph, actual_max_size, 0)
                    chunks.extend(para_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"Paragraph chunking produced {len(chunks)} chunks")
        return chunks