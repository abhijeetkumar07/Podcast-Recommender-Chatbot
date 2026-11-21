import json
import logging
from typing import List, Dict, Any, Optional
from database.vector_store import VectorStoreManager
from services.podcast_service import PodcastService
from ai.llm import get_llm
from utils.validators import sanitize_string

logger = logging.getLogger(__name__)

class RAGService:

    @classmethod
    def answer_question(
        cls,
        question: str,
        podcast_id: Optional[str] = None,
        episode_title: Optional[str] = None,
        episode_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves grounded context from ChromaDB and episode metadata to answer questions.
        Explicitly identifies missing information without hallucinations.
        """
        clean_q = sanitize_string(question)
        context_snippets = []
        sources = []

        # 1. If episode description is provided directly
        if episode_description:
            context_snippets.append(f"Episode: {episode_title}\nShow Notes: {episode_description}")
            sources.append({"type": "episode_description", "title": episode_title or "Episode Details"})

        # 2. Retrieve semantic context from ChromaDB
        semantic_docs = VectorStoreManager.semantic_search(clean_q, n_results=3)
        for doc in semantic_docs:
            context_snippets.append(f"Podcast Title: {doc.get('title')}\nPublisher: {doc.get('publisher')}\nDetails: {doc.get('document')}")
            sources.append({
                "type": "podcast_metadata",
                "title": doc.get("title"),
                "id": doc.get("id"),
                "external_url": doc.get("external_url")
            })

        grounded_context = "\n\n---\n\n".join(context_snippets)

        llm = get_llm(temperature=0.2)
        if llm:
            try:
                system_prompt = f"""You are PodcastGPT RAG Assistant. 
Answer the user's question strictly using the provided Context.
If the context does not contain enough information to answer definitively, clearly state what is missing rather than guessing.
Never claim you listened to full audio if you only have show notes.

Context:
{grounded_context}

Question: {clean_q}
"""
                response = llm.invoke(system_prompt)
                answer = response.content if hasattr(response, "content") else str(response)
                return {
                    "answer": answer,
                    "grounded": True,
                    "sources": sources
                }
            except Exception as e:
                logger.error(f"RAG LLM error: {e}")

        # Deterministic Grounded Fallback
        return {
            "answer": f"Based on the available verified podcast metadata and show notes for '{clean_q}': We located {len(sources)} related verified podcast records. The summaries discuss: {context_snippets[0][:300] if context_snippets else 'No direct transcript text available in free public feeds.'}",
            "grounded": True,
            "sources": sources
        }
