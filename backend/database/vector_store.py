import os
import chromadb
from chromadb.config import Settings
import logging
from typing import List, Dict, Any, Optional
from config import config

logger = logging.getLogger(__name__)

class VectorStoreManager:
    _client = None
    _collection = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            persist_dir = config.CHROMA_PERSIST_DIR
            os.makedirs(persist_dir, exist_ok=True)
            cls._client = chromadb.PersistentClient(path=persist_dir)
        return cls._client

    @classmethod
    def get_collection(cls, collection_name: str = "podcasts"):
        if cls._collection is None:
            client = cls.get_client()
            cls._collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return cls._collection

    @classmethod
    def index_podcasts(cls, podcasts: List[Dict[str, Any]]):
        """
        Stores podcast metadata into ChromaDB using stable podcast IDs to avoid duplicates.
        """
        if not podcasts:
            return

        collection = cls.get_collection()
        ids = []
        documents = []
        metadatas = []

        for p in podcasts:
            pid = str(p.get("id"))
            if not pid:
                continue
            
            # Rich document text for semantic similarity
            doc_text = f"Title: {p.get('title', '')}. Publisher: {p.get('publisher', '')}. Genre: {p.get('genre', '')}. Topics: {', '.join(p.get('topics', []))}. Description: {p.get('description', '')}"
            
            ids.append(pid)
            documents.append(doc_text)
            metadatas.append({
                "title": str(p.get("title", "")),
                "publisher": str(p.get("publisher", "")),
                "genre": str(p.get("genre", "General")),
                "episodes": int(p.get("episodes", 0) or 0),
                "image_url": str(p.get("image_url", "")),
                "external_url": str(p.get("external_url", "")),
                "source": str(p.get("source", "itunes"))
            })

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Indexed/Upserted {len(ids)} podcasts in ChromaDB.")
        except Exception as e:
            logger.error(f"Error upserting to ChromaDB: {e}")

    @classmethod
    def semantic_search(cls, query: str, n_results: int = 10, where_filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search against indexed podcasts.
        """
        collection = cls.get_collection()
        try:
            count = collection.count()
            if count == 0:
                return []

            kwargs = {
                "query_texts": [query],
                "n_results": min(n_results, count)
            }
            if where_filter:
                kwargs["where"] = where_filter

            results = collection.query(**kwargs)
            
            formatted = []
            if results and results.get("ids") and results["ids"][0]:
                for idx, pid in enumerate(results["ids"][0]):
                    meta = results["metadatas"][0][idx] if results.get("metadatas") else {}
                    distance = results["distances"][0][idx] if results.get("distances") else 0.5
                    
                    # Cosine distance to similarity percentage score
                    similarity_score = round(max(0.0, 1.0 - distance) * 100, 1)

                    formatted.append({
                        "id": pid,
                        "title": meta.get("title", "Unknown"),
                        "publisher": meta.get("publisher", "Unknown"),
                        "genre": meta.get("genre", "General"),
                        "episodes": meta.get("episodes", 0),
                        "image_url": meta.get("image_url", ""),
                        "external_url": meta.get("external_url", "#"),
                        "similarity_score": similarity_score,
                        "document": results["documents"][0][idx] if results.get("documents") else ""
                    })
            return formatted
        except Exception as e:
            logger.error(f"Semantic search query error: {e}")
            return []
