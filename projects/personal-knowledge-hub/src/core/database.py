"""
Core database interface for Personal Knowledge Hub.
Handles ChromaDB operations and collection management.
"""

import os
import logging
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeHubDatabase:
    """Interface to ChromaDB for knowledge storage and retrieval."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the database with configuration."""
        self.config = self._load_config(config_path)
        self.persist_directory = self.config["database"]["persist_directory"]
        self.distance_metric = self.config["database"]["distance_metric"]
        
        # Ensure persistence directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        logger.info(f"Initialized ChromaDB client with persistence at {self.persist_directory}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Get existing collection or create a new one."""
        try:
            collection = self.client.get_collection(name=name)
            logger.info(f"Retrieved existing collection: {name}")
        except ValueError:
            # Collection doesn't exist, create it
            collection = self.client.create_collection(
                name=name,
                metadata={"hnsw:space": self.distance_metric}
            )
            logger.info(f"Created new collection: {name}")
        return collection
    
    def add_documents(
        self, 
        collection_name: str, 
        documents: List[str], 
        embeddings: List[List[float]], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs
        """
        collection = self.get_or_create_collection(collection_name)
        
        # Generate IDs if not provided
        if ids is None:
            start_id = collection.count() if collection.count() > 0 else 0
            ids = [f"doc_{start_id + i}" for i in range(len(documents))]
        
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
    
    def query(
        self, 
        collection_name: str, 
        query_embeddings: List[List[float]], 
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query a collection for similar documents.
        
        Args:
            collection_name: Name of the collection to query
            query_embeddings: List of query embedding vectors
            n_results: Number of results to return
            where: Metadata filter (e.g., {"source": "web"})
            where_document: Document content filter
            
        Returns:
            Dictionary with keys: ids, distances, metadatas, documents
        """
        collection = self.get_or_create_collection(collection_name)
        
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        logger.info(f"Queried collection '{collection_name}' with {len(query_embeddings)} queries")
        return results
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection."""
        collection = self.get_or_create_collection(collection_name)
        return {
            "name": collection_name,
            "count": collection.count(),
            "metadata": collection.metadata
        }
    
    def list_collections(self) -> List[str]:
        """List all available collections."""
        return [col.name for col in self.client.list_collections()]
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except ValueError:
            logger.warning(f"Collection '{collection_name}' does not exist")
    
    def peek_collection(self, collection_name: str, limit: int = 10) -> Dict[str, Any]:
        """Peek at the first few documents in a collection."""
        collection = self.get_or_create_collection(collection_name)
        return collection.peek(limit=limit)