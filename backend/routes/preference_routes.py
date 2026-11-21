from flask import Blueprint, request, jsonify
import logging
from services.personalization_service import PersonalizationService

logger = logging.getLogger(__name__)
preference_bp = Blueprint("preferences", __name__)

@preference_bp.route("", methods=["GET"])
def get_preferences():
    user_id = request.args.get("user_id", "guest_user")
    prefs = PersonalizationService.get_user_preferences(user_id)
    return jsonify(prefs), 200

@preference_bp.route("", methods=["PUT"])
def update_preferences():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "guest_user")
    success = PersonalizationService.update_user_preferences(user_id, data)
    if success:
        return jsonify({"status": "updated", "preferences": data}), 200
    return jsonify({"error": "Failed to update preferences"}), 500

@preference_bp.route("/saved", methods=["GET"])
def get_saved():
    user_id = request.args.get("user_id", "guest_user")
    saved = PersonalizationService.get_saved_podcasts(user_id)
    return jsonify({"user_id": user_id, "saved_podcasts": saved}), 200

@preference_bp.route("/save", methods=["POST"])
def save():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "guest_user")
    success = PersonalizationService.save_podcast(user_id, data)
    if success:
        return jsonify({"status": "saved"}), 200
    return jsonify({"error": "Failed to save podcast"}), 500

@preference_bp.route("/save", methods=["DELETE"])
def remove_saved():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "guest_user")
    podcast_id = data.get("podcast_id")
    if not podcast_id:
        return jsonify({"error": "podcast_id is required"}), 400

    success = PersonalizationService.remove_saved_podcast(user_id, podcast_id)
    if success:
        return jsonify({"status": "removed"}), 200
    return jsonify({"error": "Failed to remove saved podcast"}), 500
