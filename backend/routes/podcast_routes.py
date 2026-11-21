from flask import Blueprint, request, jsonify
import logging
from services.podcast_service import PodcastService
from services.recommendation_service import RecommendationService
from utils.validators import validate_search_query

logger = logging.getLogger(__name__)
podcast_bp = Blueprint("podcasts", __name__)

@podcast_bp.route("/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "")
    valid, result = validate_search_query(query)
    if not valid:
        return jsonify({"error": result}), 400

    try:
        limit = int(data.get("limit", 15))
    except (ValueError, TypeError):
        limit = 15

    podcasts = PodcastService.search_podcasts(result, limit=limit)
    return jsonify({
        "query": result,
        "count": len(podcasts),
        "results": podcasts
    }), 200

@podcast_bp.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "")
    valid, result = validate_search_query(query)
    if not valid:
        return jsonify({"error": result}), 400

    try:
        limit = int(data.get("limit", 10))
    except (ValueError, TypeError):
        limit = 10

    user_preferences = data.get("preferences", None)
    
    recommendations = RecommendationService.get_recommendations(
        query=result,
        user_preferences=user_preferences,
        limit=limit
    )
    return jsonify({
        "query": result,
        "count": len(recommendations),
        "results": recommendations
    }), 200

@podcast_bp.route("/<podcast_id>", methods=["GET"])
def get_details(podcast_id: str):
    if not podcast_id:
        return jsonify({"error": "Podcast ID is required"}), 400

    details = PodcastService.get_podcast_details(podcast_id)
    if not details:
        return jsonify({"error": "Podcast not found or feed unreachable"}), 404

    return jsonify(details), 200
