import uuid
import json
import logging
from typing import List, Dict, Any, Optional
from services.podcast_service import PodcastService
from database.sqlite_store import get_db_connection
from ai.llm import get_llm

logger = logging.getLogger(__name__)

class LearningPathService:

    CURATED_SYLLABI = {
        "generative ai": [
            {"stage": 1, "topic": "AI & Data Fundamentals", "query": "AI Fundamentals Data Science"},
            {"stage": 2, "topic": "Machine Learning Foundations", "query": "Machine Learning Guide"},
            {"stage": 3, "topic": "Deep Learning & Neural Networks", "query": "Deep Learning Neural Networks"},
            {"stage": 4, "topic": "Large Language Models & Transformers", "query": "Large Language Models LLM"},
            {"stage": 5, "topic": "RAG & Vector Databases", "query": "Vector Database RAG"},
            {"stage": 6, "topic": "Autonomous AI Agents", "query": "AI Agents Autonomous Systems"}
        ],
        "machine learning": [
            {"stage": 1, "topic": "Python for Data Science", "query": "Python Data Science"},
            {"stage": 2, "topic": "Supervised & Unsupervised Learning", "query": "Machine Learning Algorithms"},
            {"stage": 3, "topic": "Model Evaluation & Deployment", "query": "MLOps Machine Learning Production"},
            {"stage": 4, "topic": "Real-world AI Case Studies", "query": "Artificial Intelligence in Industry"}
        ],
        "startup": [
            {"stage": 1, "topic": "Idea Validation & Problem Discovery", "query": "Startup Ideas Validation"},
            {"stage": 2, "topic": "Product-Market Fit & MVP", "query": "Building Minimum Viable Product"},
            {"stage": 3, "topic": "Fundraising & Pitching", "query": "Venture Capital Angel Investing"},
            {"stage": 4, "topic": "Growth, Scaling & Lessons from Failures", "query": "Startup Failure Post Mortem Scaling"}
        ]
    }

    @classmethod
    def generate_journey(cls, user_id: str, goal: str) -> Dict[str, Any]:
        """
        Creates an ordered learning roadmap where each stage links to real, retrieved podcast content.
        """
        goal_lower = goal.lower()
        journey_id = str(uuid.uuid4())
        stages_template = None

        for key, template in cls.CURATED_SYLLABI.items():
            if key in goal_lower:
                stages_template = template
                break

        if not stages_template:
            # Generate stages dynamically
            stages_template = [
                {"stage": 1, "topic": f"{goal} - Foundations & Core Concepts", "query": f"{goal} 101 basics"},
                {"stage": 2, "topic": f"{goal} - Intermediate Practical Implementations", "query": f"{goal} practical guide"},
                {"stage": 3, "topic": f"{goal} - Masterclasses & Industry Expert Discussions", "query": f"{goal} advanced masterclass"}
            ]

        resolved_stages = []
        for step in stages_template:
            # Fetch real podcasts for this specific step
            podcasts = PodcastService.search_podcasts(step["query"], limit=2)
            recommended_podcasts = []
            for p in podcasts:
                recommended_podcasts.append({
                    "id": p["id"],
                    "title": p["title"],
                    "publisher": p["publisher"],
                    "image_url": p["image_url"],
                    "external_url": p["external_url"]
                })

            resolved_stages.append({
                "stage_index": step["stage"],
                "topic": step["topic"],
                "search_query": step["query"],
                "completed": False,
                "recommended_podcasts": recommended_podcasts
            })

        # Save to SQLite
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            # Ensure user exists
            cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, f"user_{user_id}"))
            cursor.execute("""
                INSERT INTO learning_journeys (id, user_id, goal, stages)
                VALUES (?, ?, ?, ?)
            """, (journey_id, user_id, goal, json.dumps(resolved_stages)))
            conn.commit()
        except Exception as e:
            logger.error(f"Error persisting learning journey: {e}")
        finally:
            conn.close()

        return {
            "journey_id": journey_id,
            "goal": goal,
            "stages": resolved_stages
        }

    @classmethod
    def update_progress(cls, journey_id: str, stage_index: int, completed: bool) -> bool:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_progress (journey_id, stage_index, completed, completed_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(journey_id, stage_index) DO UPDATE SET
                    completed=excluded.completed,
                    completed_at=CURRENT_TIMESTAMP
            """, (journey_id, stage_index, 1 if completed else 0))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating learning progress: {e}")
            return False
        finally:
            conn.close()
