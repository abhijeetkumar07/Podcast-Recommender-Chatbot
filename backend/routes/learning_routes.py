from flask import Blueprint, request, jsonify
import logging
from services.learning_path_service import LearningPathService

logger = logging.getLogger(__name__)
learning_bp = Blueprint("learning", __name__)

@learning_bp.route("", methods=["POST"])
def create_journey():
    data = request.get_json(silent=True) or {}
    goal = data.get("goal", "").strip()
    if not goal:
        return jsonify({"error": "A learning goal is required, e.g. 'Learn Generative AI'"}), 400

    user_id = data.get("user_id", "guest_user")
    journey = LearningPathService.generate_journey(user_id=user_id, goal=goal)
    return jsonify(journey), 201

@learning_bp.route("/progress", methods=["PUT"])
def update_progress():
    data = request.get_json(silent=True) or {}
    journey_id = data.get("journey_id")
    stage_index = data.get("stage_index")
    completed = bool(data.get("completed", False))

    if not journey_id or stage_index is None:
        return jsonify({"error": "journey_id and stage_index are required"}), 400

    try:
        stage_idx = int(stage_index)
    except (ValueError, TypeError):
        return jsonify({"error": "stage_index must be an integer"}), 400

    success = LearningPathService.update_progress(journey_id, stage_idx, completed)
    if success:
        return jsonify({"status": "updated", "journey_id": journey_id, "stage_index": stage_idx, "completed": completed}), 200
    return jsonify({"error": "Failed to update learning progress"}), 500
