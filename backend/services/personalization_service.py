import json
import logging
from typing import List, Dict, Any, Optional
from database.sqlite_store import get_db_connection

logger = logging.getLogger(__name__)

class PersonalizationService:

    @classmethod
    def get_user_preferences(cls, user_id: str) -> Dict[str, Any]:
        conn = get_db_connection()
        row = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
        finally:
            conn.close()

        if row:
            return {
                "user_id": row["user_id"],
                "interests": json.loads(row["interests"]) if row["interests"] else [],
                "preferred_topics": json.loads(row["preferred_topics"]) if row["preferred_topics"] else [],
                "learning_level": row["learning_level"] or "Intermediate",
                "preferred_language": row["preferred_language"] or "English",
                "preferred_duration": row["preferred_duration"] or "Any",
                "professional_goals": row["professional_goals"] or ""
            }
        
        # Defaults
        return {
            "user_id": user_id,
            "interests": ["AI & Tech", "Engineering"],
            "preferred_topics": ["Generative AI", "Software Architecture"],
            "learning_level": "Intermediate",
            "preferred_language": "English",
            "preferred_duration": "Any",
            "professional_goals": "Master AI Engineering and Placement Preparation"
        }

    @classmethod
    def update_user_preferences(cls, user_id: str, data: Dict[str, Any]) -> bool:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, f"user_{user_id}"))
            
            interests_json = json.dumps(data.get("interests", []))
            topics_json = json.dumps(data.get("preferred_topics", []))

            cursor.execute("""
                INSERT INTO user_preferences (user_id, interests, preferred_topics, learning_level, preferred_language, preferred_duration, professional_goals)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    interests=excluded.interests,
                    preferred_topics=excluded.preferred_topics,
                    learning_level=excluded.learning_level,
                    preferred_language=excluded.preferred_language,
                    preferred_duration=excluded.preferred_duration,
                    professional_goals=excluded.professional_goals,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                user_id,
                interests_json,
                topics_json,
                data.get("learning_level", "Intermediate"),
                data.get("preferred_language", "English"),
                data.get("preferred_duration", "Any"),
                data.get("professional_goals", "")
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    def get_saved_podcasts(cls, user_id: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM saved_podcasts WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @classmethod
    def save_podcast(cls, user_id: str, podcast_data: Dict[str, Any]) -> bool:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, f"user_{user_id}"))
            cursor.execute("""
                INSERT INTO saved_podcasts (user_id, podcast_id, title, publisher, image_url, genre, external_url, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, podcast_id) DO NOTHING
            """, (
                user_id,
                str(podcast_data.get("podcast_id") or podcast_data.get("id")),
                podcast_data.get("title", "Untitled Podcast"),
                podcast_data.get("publisher", ""),
                podcast_data.get("image_url", ""),
                podcast_data.get("genre", ""),
                podcast_data.get("external_url", "#"),
                podcast_data.get("notes", "")
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving podcast: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    def remove_saved_podcast(cls, user_id: str, podcast_id: str) -> bool:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM saved_podcasts WHERE user_id = ? AND podcast_id = ?", (user_id, podcast_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing saved podcast: {e}")
            return False
        finally:
            conn.close()
