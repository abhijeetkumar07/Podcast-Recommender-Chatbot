from flask import Blueprint, request, jsonify
import logging
from services.summarization_service import SummarizationService
from services.rag_service import RAGService

logger = logging.getLogger(__name__)
episode_bp = Blueprint("episodes", __name__)

@episode_bp.route("/summarize", methods=["POST"])
def summarize():
    data = request.get_json(silent=True) or {}
    episode_title = data.get("episode_title", "Untitled Episode")
    episode_description = data.get("episode_description", "")
    podcast_title = data.get("podcast_title", "")

    summary = SummarizationService.summarize_episode(
        episode_title=episode_title,
        episode_description=episode_description,
        podcast_title=podcast_title
    )
    return jsonify(summary), 200

@episode_bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question parameter is required"}), 400

    podcast_id = data.get("podcast_id")
    episode_title = data.get("episode_title")
    episode_description = data.get("episode_description")

    answer_data = RAGService.answer_question(
        question=question,
        podcast_id=podcast_id,
        episode_title=episode_title,
        episode_description=episode_description
    )
    return jsonify(answer_data), 200
