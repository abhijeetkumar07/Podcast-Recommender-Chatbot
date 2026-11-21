import json
import logging
from typing import List, Dict, Any, Optional
from services.podcast_service import PodcastService
from services.recommendation_service import RecommendationService
from services.personalization_service import PersonalizationService
from services.summarization_service import SummarizationService
from database.sqlite_store import get_db_connection
from ai.llm import get_llm

logger = logging.getLogger(__name__)

class PodcastGPTAgent:

    @classmethod
    def search_podcasts(cls, query: str) -> str:
        """Tool 1: Searches podcasts using genuine Apple iTunes metadata."""
        podcasts = PodcastService.search_podcasts(query, limit=5)
        return json.dumps(podcasts)

    @classmethod
    def recommend_podcasts(cls, query: str, user_id: str = "guest_user") -> str:
        """Tool 2: Computes hybrid recommendation ranking with match scores."""
        prefs = PersonalizationService.get_user_preferences(user_id)
        results = RecommendationService.get_recommendations(query=query, user_preferences=prefs, limit=5)
        return json.dumps(results)

    @classmethod
    def search_episode_knowledge(cls, podcast_id: str) -> str:
        """Tool 3: Retrieves verified episode metadata and RSS show notes."""
        details = PodcastService.get_podcast_details(podcast_id)
        if details:
            return json.dumps({
                "title": details.get("title"),
                "episodes_sample": details.get("episodes", [])[:3]
            })
        return json.dumps({"error": "Podcast details not found"})

    @classmethod
    def summarize_episode(cls, episode_title: str, episode_description: str) -> str:
        """Tool 4: Generates a grounded structured summary of an episode's notes."""
        summary = SummarizationService.summarize_episode(episode_title, episode_description)
        return json.dumps(summary)

    @classmethod
    def get_user_preferences(cls, user_id: str) -> str:
        """Tool 5: Reads user profile preferences and learning level."""
        prefs = PersonalizationService.get_user_preferences(user_id)
        return json.dumps(prefs)

    @classmethod
    def save_podcast(cls, user_id: str, podcast_id: str, title: str) -> str:
        """Tool 6: Saves a podcast to the user's library."""
        success = PersonalizationService.save_podcast(user_id, {"id": podcast_id, "title": title})
        return json.dumps({"status": "saved" if success else "failed"})

    @classmethod
    def process_message(cls, conversation_id: str, user_id: str, message: str) -> Dict[str, Any]:
        """
        Coordinates the conversational assistant with conversational memory & approved tool executions.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            # 1. Fetch recent conversation short-term memory (last 6 messages)
            cursor.execute("""
                SELECT role, content FROM messages 
                WHERE conversation_id = ? 
                ORDER BY created_at DESC LIMIT 6
            """, (conversation_id,))
            recent_rows = cursor.fetchall()
            recent_history = list(reversed([{"role": r["role"], "content": r["content"]} for r in recent_rows]))

            # Record incoming user message
            cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, f"user_{user_id}"))
            cursor.execute("INSERT OR IGNORE INTO conversations (id, user_id) VALUES (?, ?)", (conversation_id, user_id))
            cursor.execute("""
                INSERT INTO messages (conversation_id, role, content)
                VALUES (?, 'user', ?)
            """, (conversation_id, message))
            conn.commit()
        finally:
            conn.close()

        # 2. Get user preferences for long-term personalization memory
        user_prefs = PersonalizationService.get_user_preferences(user_id)

        # 3. Execute recommendations
        # Determine intent & search podcasts
        recommendations = RecommendationService.get_recommendations(
            query=message,
            user_preferences=user_prefs,
            limit=4
        )

        llm = get_llm(temperature=0.3)
        assistant_reply = ""

        if llm:
            try:
                history_prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent_history])
                rec_context = "\n".join([
                    f"- {r['title']} by {r['publisher']} (Genre: {r['genre']}, Match Score: {r['match_score']}%): {r['relevance_reason']}"
                    for r in recommendations
                ])

                prompt = f"""You are PodcastGPT, an editorial audio intelligence assistant.
User Profile: Learning Level = {user_prefs.get('learning_level')}, Language = {user_prefs.get('preferred_language')}

Recent Conversation History:
{history_prompt}

Current User Request: "{message}"

Grounded Verified Podcast Candidates:
{rec_context}

Provide an insightful, editorial, and helpful conversational response. Explain WHY each recommendation fits their goal and learning level.
If the user asks follow-up refinements (e.g. 'I am a beginner', 'make it shorter'), address that directly using the conversation history.
Keep the tone sophisticated, engaging, and precise.
"""
                resp = llm.invoke(prompt)
                assistant_reply = resp.content if hasattr(resp, "content") else str(resp)
            except Exception as e:
                logger.error(f"Agent LLM invocation error: {e}")

        if not assistant_reply:
            # Deterministic, grounded fallback response
            rec_titles = [f"**{r['title']}** ({r['match_score']}% match)" for r in recommendations[:3]]
            assistant_reply = f"Here are the top-rated shows matching your interests in **{message}** at the **{user_prefs.get('learning_level', 'Intermediate')}** level: {', '.join(rec_titles)}. Explore their show notes or ask questions about specific episodes below."

        # Save assistant message to memory
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            metadata_json = json.dumps({"recommendations_count": len(recommendations)})
            cursor.execute("""
                INSERT INTO messages (conversation_id, role, content, metadata)
                VALUES (?, 'assistant', ?, ?)
            """, (conversation_id, assistant_reply, metadata_json))
            conn.commit()
        finally:
            conn.close()

        return {
            "conversation_id": conversation_id,
            "reply": assistant_reply,
            "recommendations": recommendations,
            "suggested_follow_ups": [
                "Which of these has beginner-friendly episodes?",
                "Give me a structured summary of the latest episode",
                "Create a step-by-step learning journey for this"
            ]
        }
