import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import config

# Import Routes
from routes.podcast_routes import podcast_bp
from routes.chat_routes import chat_bp
from routes.episode_routes import episode_bp
from routes.preference_routes import preference_bp
from routes.learning_routes import learning_bp
from services.recommendation_service import RecommendationService
from database.sqlite_store import init_db

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not config.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # Initialize SQLite Database
    init_db()

    # Configure CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register Blueprints
    app.register_blueprint(podcast_bp, url_prefix="/api/podcasts")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(episode_bp, url_prefix="/api/episodes")
    app.register_blueprint(preference_bp, url_prefix="/api/preferences")
    app.register_blueprint(learning_bp, url_prefix="/api/learning-path")

    # PRESERVED BACKWARD COMPATIBILITY ENDPOINTS FOR EXISTING FRONTEND
    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "service": "PodcastGPT API",
            "version": "2.0.0",
            "status": "online",
            "endpoints": [
                "/api/podcasts/search",
                "/api/podcasts/recommend",
                "/api/chat",
                "/api/chat/history",
                "/api/episodes/summarize",
                "/api/episodes/ask",
                "/api/preferences",
                "/api/preferences/saved",
                "/api/learning-path",
                "/recommend (legacy preserved)"
            ]
        })

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": "PodcastGPT"}), 200

    @app.route("/recommend", methods=["POST"])
    def legacy_recommend():
        """
        Preserves complete backward compatibility with the original frontend while adding
        hybrid scoring and sanitization.
        """
        try:
            data = request.get_json(silent=True) or {}
            user_input = data.get("query", "").strip()
            if not user_input:
                return jsonify({"error": "Query not provided"}), 400

            recommendations = RecommendationService.get_recommendations(query=user_input, limit=10)
            
            # Format exactly as original frontend expects
            legacy_format = []
            for r in recommendations:
                legacy_format.append({
                    "id": str(r.get("id", "")),
                    "title": r.get("title", "Unknown Title"),
                    "description": r.get("description", ""),
                    "publisher": r.get("publisher", "Unknown Publisher"),
                    "episodes": r.get("episodes", 0),
                    "image_url": r.get("image_url", ""),
                    "topics": r.get("topics", ["Podcast"]),
                    "external_url": r.get("external_url", "#"),
                    "match_score": r.get("match_score", 80),
                    "relevance_reason": r.get("relevance_reason", "")
                })
            return jsonify(legacy_format)
        except Exception as e:
            logger.error(f"Legacy recommend endpoint error: {e}")
            return jsonify({"error": str(e)}), 500

    # Global Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def handle_server_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({"error": "An unexpected server error occurred."}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    logger.info(f"Starting PodcastGPT server on {config.HOST}:{config.PORT}...")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
