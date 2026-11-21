import re
import logging
from typing import List, Dict, Any, Optional
from services.podcast_service import PodcastService
from database.vector_store import VectorStoreManager
from ai.structured_outputs import QueryUnderstanding

logger = logging.getLogger(__name__)

class RecommendationService:

    @classmethod
    def calculate_hybrid_score(
        cls,
        podcast: Dict[str, Any],
        query: str,
        query_analysis: Optional[QueryUnderstanding] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        semantic_score: float = 70.0
    ) -> float:
        """
        Pure Python transparent weighted scoring:
        - Keyword relevance in Title & Publisher (30%)
        - Semantic Vector Similarity (35%)
        - Genre & Topic Alignment (20%)
        - User Learning Level & Preferences (15%)
        """
        q_lower = query.lower()
        title_lower = podcast.get("title", "").lower()
        publisher_lower = podcast.get("publisher", "").lower()
        genre_lower = podcast.get("genre", "").lower()

        # 1. Keyword match (0 to 30)
        kw_score = 0.0
        query_words = [w for w in re.split(r'\W+', q_lower) if len(w) > 2]
        if query_words:
            matched_words = sum(1 for w in query_words if w in title_lower or w in publisher_lower)
            kw_score = (matched_words / len(query_words)) * 30.0

        # 2. Semantic score (0 to 35)
        # Normalized from 0-100 to 0-35
        sem_component = (semantic_score / 100.0) * 35.0

        # 3. Genre & Topic match (0 to 20)
        genre_score = 10.0 # base default
        if query_analysis and query_analysis.subtopics:
            matched_topics = sum(1 for sub in query_analysis.subtopics if sub.lower() in title_lower or sub.lower() in genre_lower)
            if matched_topics > 0:
                genre_score = 20.0
        elif any(w in genre_lower for w in query_words):
            genre_score = 18.0

        # 4. User Preference / Learning Level (0 to 15)
        pref_score = 10.0
        if user_preferences:
            pref_topics = [t.lower() for t in user_preferences.get("preferred_topics", [])]
            if any(t in title_lower or t in genre_lower for t in pref_topics):
                pref_score += 5.0
            
            # Check level fit
            user_level = user_preferences.get("learning_level", "Intermediate").lower()
            if user_level == "beginner" and any(b in title_lower for b in ["101", "basics", "starter", "intro"]):
                pref_score += 3.0

        total_score = round(min(100.0, kw_score + sem_component + genre_score + pref_score), 1)
        return total_score

    @classmethod
    def get_recommendations(
        cls,
        query: str,
        query_analysis: Optional[QueryUnderstanding] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieves real podcasts via iTunes and Semantic ChromaDB, computes hybrid score,
        and generates genuine relevance reasons.
        """
        # Fetch real podcasts
        live_podcasts = PodcastService.search_podcasts(query, limit=15)
        
        # Index in ChromaDB for persistent vector retrieval
        if live_podcasts:
            VectorStoreManager.index_podcasts(live_podcasts)

        # Also get semantic matches from Chroma
        semantic_matches = VectorStoreManager.semantic_search(query, n_results=10)
        semantic_dict = {str(item["id"]): item.get("similarity_score", 65.0) for item in semantic_matches}

        # Combine results avoiding duplicates
        all_candidates = {p["id"]: p for p in live_podcasts}
        for sem in semantic_matches:
            if sem["id"] not in all_candidates:
                all_candidates[sem["id"]] = sem

        ranked = []
        for pid, pod in all_candidates.items():
            sem_score = semantic_dict.get(pid, 70.0)
            score = cls.calculate_hybrid_score(
                podcast=pod,
                query=query,
                query_analysis=query_analysis,
                user_preferences=user_preferences,
                semantic_score=sem_score
            )
            
            # Generate transparent reasoning
            reasons = []
            if sem_score > 75:
                reasons.append("High semantic alignment with your search intention")
            if any(w in pod.get("title", "").lower() for w in query.lower().split() if len(w) > 3):
                reasons.append("Direct keyword match in series title")
            if pod.get("episodes", 0) > 20:
                reasons.append(f"Established catalog with {pod.get('episodes')} verified episodes")
            if not reasons:
                reasons.append(f"Curated match in {pod.get('genre', 'Podcast')} category")

            pod_copy = dict(pod)
            pod_copy["match_score"] = score
            pod_copy["relevance_reason"] = " • ".join(reasons)
            ranked.append(pod_copy)

        # Sort descending by match score
        ranked.sort(key=lambda x: x["match_score"], reverse=True)
        return ranked[:limit]
