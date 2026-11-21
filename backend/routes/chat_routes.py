from flask import Blueprint, request, jsonify
import uuid
import logging
from ai.agent import PodcastGPTAgent
from database.sqlite_store import get_db_connection

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)

@chat_bp.route("", methods=["POST"])
def send_chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
    user_id = data.get("user_id") or "guest_user"

    result = PodcastGPTAgent.process_message(
        conversation_id=conversation_id,
        user_id=user_id,
        message=message
    )
    return jsonify(result), 200

@chat_bp.route("/history", methods=["GET"])
def get_history():
    conversation_id = request.args.get("conversation_id")
    if not conversation_id:
        return jsonify({"error": "conversation_id query parameter is required."}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, metadata, created_at 
            FROM messages 
            WHERE conversation_id = ? 
            ORDER BY created_at ASC
        """, (conversation_id,))
        rows = cursor.fetchall()
        history = [dict(r) for r in rows]
        return jsonify({"conversation_id": conversation_id, "messages": history}), 200
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({"error": "Failed to fetch chat history"}), 500
    finally:
        conn.close()

@chat_bp.route("/history", methods=["DELETE"])
def clear_history():
    conversation_id = request.args.get("conversation_id")
    if not conversation_id:
        return jsonify({"error": "conversation_id query parameter is required."}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        return jsonify({"status": "cleared", "conversation_id": conversation_id}), 200
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return jsonify({"error": "Failed to clear chat history"}), 500
    finally:
        conn.close()
