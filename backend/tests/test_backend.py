import pytest
import json
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app import create_app
from services.podcast_service import PodcastService
from services.recommendation_service import RecommendationService
from services.summarization_service import SummarizationService

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"

def test_podcast_search_live():
    results = PodcastService.search_podcasts("Technology", limit=3)
    assert isinstance(results, list)
    if len(results) > 0:
        assert "id" in results[0]
        assert "title" in results[0]
        assert "publisher" in results[0]

def test_recommendation_scoring():
    sample_pod = {
        "title": "Machine Learning Guide",
        "publisher": "OCDevel",
        "genre": "Technology",
        "episodes": 40
    }
    score = RecommendationService.calculate_hybrid_score(
        podcast=sample_pod,
        query="Machine Learning",
        semantic_score=85.0
    )
    assert 0.0 <= score <= 100.0
    assert score > 50.0

def test_summarization_deterministic():
    desc = "In this episode, we talk about building autonomous agents using LangChain and Python. Key ideas include memory and tools."
    summary = SummarizationService.summarize_episode("Building Agents", desc)
    assert "short_overview" in summary
    assert "key_takeaways" in summary
    assert len(summary["key_takeaways"]) > 0

def test_legacy_recommend_endpoint(client):
    response = client.post("/recommend", json={"query": "AI"})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

def test_safe_parameter_coercion(client):
    # Pass invalid non-numeric limit, should not crash with 500
    res = client.post("/api/podcasts/search", json={"query": "AI", "limit": "invalid"})
    assert res.status_code == 200
    
    res2 = client.post("/api/podcasts/recommend", json={"query": "AI", "limit": "invalid"})
    assert res2.status_code == 200

def test_chat_and_user_collision_resistance(client):
    res1 = client.post("/api/chat", json={"message": "recommend podcast", "user_id": "guest_user_a", "conversation_id": "conv_a"})
    assert res1.status_code == 200

    res2 = client.post("/api/chat", json={"message": "recommend podcast", "user_id": "guest_user_b", "conversation_id": "conv_b"})
    assert res2.status_code == 200

    hist_res = client.get("/api/chat/history?conversation_id=conv_a")
    assert hist_res.status_code == 200
    assert len(hist_res.get_json()["messages"]) >= 2

def test_user_preferences_flow(client):
    put_res = client.put("/api/preferences", json={
        "user_id": "test_pref_user",
        "learning_level": "Advanced",
        "preferred_topics": ["Deep Learning", "Transformers"]
    })
    assert put_res.status_code == 200

    get_res = client.get("/api/preferences?user_id=test_pref_user")
    assert get_res.status_code == 200
    prefs = get_res.get_json()
    assert prefs["learning_level"] == "Advanced"
    assert "Deep Learning" in prefs["preferred_topics"]

def test_learning_journey_and_progress(client):
    create_res = client.post("/api/learning-path", json={
        "goal": "Machine Learning",
        "user_id": "test_learn_user"
    })
    assert create_res.status_code == 201
    journey = create_res.get_json()
    assert "journey_id" in journey
    assert len(journey["stages"]) > 0

    prog_res = client.put("/api/learning-path/progress", json={
        "journey_id": journey["journey_id"],
        "stage_index": "1",
        "completed": True
    })
    assert prog_res.status_code == 200
