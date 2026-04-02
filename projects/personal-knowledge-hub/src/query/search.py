"""
Search interface for Personal Knowledge Hub.
Handles querying the knowledge base with natural language.
"""

import logging
from typing import List, Dict, Any, Optional
from src.core.database import KnowledgeHubDatabase
from src.core.embeddings import EmbeddingManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeSearch:
    """Interface for searching the knowledge hub."""
    
    def __init__(
        self, 
        database: KnowledgeHubDatabase, 
        embedding_manager: EmbeddingManager,
        config_path: str = "config/settings.yaml"
    ):
        """Initialize the search interface."""
        self.database = database
        self.embedding_manager = embedding_manager
        self.config = self._load_config(config_path)
        self.top_k = self.config["query"]["top_k"]
        self.min_similarity = self.config["query"]["min_similarity"]
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def search(
        self, 
        query_text: str, 
        collection_name: str = "default",
        top_k: Optional[int] = None,
        min_similarity: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query_text: Natural language query
            collection_name: Name of the collection to search
            top_k: Number of results to return (overrides config if provided)
            min_similarity: Minimum similarity threshold (overrides config if provided)
            metadata_filter: Filter results by metadata (e.g., {"source": "web"})
            
        Returns:
            List of result dictionaries with keys: id, score, metadata, document
        """
        try:
            # Generate embedding for query
            query_embedding = self.embedding_manager.embed_texts([query_text])[0]
            
            # Query the database
            actual_top_k = top_k if top_k is not None else self.top_k
            results = self.database.query(
                collection_name=collection_name,
                query_embeddings=[query_embedding],
                n_results=actual_top_k,
                where=metadata_filter
            )
            
            # Process results
            processed_results = []
            actual_min_similarity = min_similarity if min_similarity is not None else self.min_similarity
            
            for i in range(len(results["ids"][0])):
                # Calculate similarity score (convert distance to similarity)
                distance = results["distances"][0][i]
                # For cosine distance, similarity = 1 - distance
                # For other metrics, this might need adjustment
                similarity = 1.0 - distance if distance <= 1.0 else 0.0
                
                if similarity >= actual_min_similarity:
                    result = {
                        "id": results["ids"][0][i],
                        "score": similarity,
                        "metadata": results["metadatas"][0][i],
                        "document": results["documents"][0][i]
                    }
                    processed_results.append(result)
            
            # Sort by score (descending)
            processed_results.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"Search returned {len(processed_results)} results above threshold")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    def get_collection_stats(self, collection_name: str = "default") -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            info = self.database.get_collection_info(collection_name)
            return {
                "collection_name": info["name"],
                "document_count": info["count"],
                "embedding_dimensions": self.embedding_manager.get_embedding_dimension(),
                "distance_metric": info["metadata"].get("hnsw:space", "unknown")
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def list_collections(self) -> List[str]:
        """List all available collections."""
        return self.database.list_collections()