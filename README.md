# PodcastGPT – AI-Powered Podcast Discovery, Intelligence, Learning & Personalization Platform

PodcastGPT transforms conventional audio discovery into a structured, production-ready AI ecosystem combining semantic search, multi-turn conversational agents, RAG (Retrieval-Augmented Generation), verified RSS show-notes summarization, and personalized learning journeys.

---

## Architecture Overview

```
PodcastGPT/
├── backend/
│   ├── app.py                     # Application factory & legacy backward compatibility
│   ├── config.py                  # Dynamic environment configuration
│   ├── routes/
│   │   ├── podcast_routes.py      # Search, lookup & recommendation endpoints
│   │   ├── chat_routes.py         # Multi-turn conversation & session memory
│   │   ├── episode_routes.py      # Summarization & RAG Q&A endpoints
│   │   ├── preference_routes.py   # User profiles & saved audio library
│   │   └── learning_routes.py     # Structured learning journeys & progress tracking
│   ├── services/
│   │   ├── podcast_service.py     # Live Apple iTunes API & RSS feed parser
│   │   ├── recommendation_service.py # Hybrid scoring engine (keyword + vector + user fit)
│   │   ├── summarization_service.py  # Grounded structured episode breakdowns
│   │   ├── rag_service.py         # Vector-retrieved Q&A with source attribution
│   │   ├── personalization_service.py# SQLite profile & bookmarks manager
│   │   └── learning_path_service.py  # Structured milestone roadmaps
│   ├── ai/
│   │   ├── llm.py                 # LangChain LLM orchestrator (Gemini / OpenAI fallback)
│   │   ├── agent.py               # Tool-calling agent with conversational short/long-term memory
│   │   └── structured_outputs.py  # Pydantic schemas for intent and summaries
│   ├── database/
│   │   ├── sqlite_store.py        # Relational schema for users, chats, bookmarks, roadmaps
│   │   └── vector_store.py        # Persistent ChromaDB cosine similarity manager
│   ├── utils/
│   │   └── validators.py          # Input validation & XSS sanitization
│   └── tests/
│       └── test_backend.py        # Pytest test suite
└── frontend/
    └── index.html                 # Editorial Audio Intelligence UI (Tailwind CSS + Lucide Icons)
```

---

## Key Features

1. **Editorial Audio Intelligence UI**: Designed with high-contrast typography (Cinzel & Plus Jakarta Sans), audio soundwave visualizations, dark ink aesthetics, and responsive layout.
2. **Transparent Hybrid Recommendation Ranking**:
   - Title & Publisher Keyword Match (30%)
   - ChromaDB Cosine Semantic Vector Score (35%)
   - Genre & Topic Alignment (20%)
   - User Learning Level & Personalization Fit (15%)
3. **Multi-Turn Conversational AI Studio**:
   - Short-term conversational window stored in SQLite.
   - Long-term memory retrieving user learning levels and interests.
   - Approved tool executions for real-time podcast discovery.
4. **Episode Intelligence Studio**:
   - Executive summaries, key takeaways, important concepts, and beginner-friendly breakdowns.
   - Clearly labeled grounding sources (e.g. *Verified RSS Show Notes*).
5. **Ask-This-Episode RAG Interface**:
   - Vector-similarity retrieval over episode content with explicit answers that do not hallucinate missing information.
6. **Structured Learning Paths**:
   - Generates sequenced learning milestones (e.g., Generative AI, Machine Learning, Startups) mapped to verified podcast episodes with progress persistence.

---

## Local Quickstart Instructions

### 1. Backend Setup
```bash
cd "ai_chatbot/ai_chatbot/backend"

# Install dependencies
pip install -r requirements.txt

# Configure your environment
cp .env.example .env
# Edit .env and insert your GOOGLE_API_KEY (optional, system includes deterministic offline fallback)

# Run the Flask API
python app.py
```
Backend will start on `http://127.0.0.1:5000`.

### 2. Frontend Launch
Simply open `ai_chatbot/ai_chatbot/frontend/index.html` in any modern web browser or serve it via:
```bash
cd "ai_chatbot/ai_chatbot/frontend"
python -m http.server 3000
```
Open `http://localhost:3000` to interact with PodcastGPT.

### 3. Run Automated Tests
```bash
python -m pytest ai_chatbot/ai_chatbot/backend/tests/test_backend.py -v
```

---

## API Endpoints Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check & service status |
| `/api/podcasts/search` | POST | Live iTunes podcast search with validation |
| `/api/podcasts/recommend` | POST | Hybrid vector + keyword ranking |
| `/api/podcasts/<id>` | GET | Detailed metadata & verified RSS episodes |
| `/api/chat` | POST | Multi-turn conversational intelligence agent |
| `/api/chat/history` | GET/DELETE | Session history management |
| `/api/episodes/summarize` | POST | Grounded structured summary generator |
| `/api/episodes/ask` | POST | Grounded RAG question answering |
| `/api/preferences` | GET/PUT | User profile & learning level settings |
| `/api/preferences/saved` | GET | User bookmarked podcast library |
| `/api/preferences/save` | POST/DELETE | Add/remove podcasts from personal library |
| `/api/learning-path` | POST | Dynamic syllabus roadmap generator |
| `/api/learning-path/progress` | PUT | Track milestone completion |
| `/recommend` | POST | **Preserved legacy endpoint** for backward compatibility |

---

## Placement Interview Explanation

> *"PodcastGPT addresses the fundamental challenge of podcast discovery: people know what concept or skill they want to learn, but search bars only match literal show titles. I transformed a basic keyword search script into a full-stack audio intelligence platform. On the backend, we implement a modular Python/Flask architecture orchestrating LangChain, ChromaDB vector search, and a transparent hybrid scoring algorithm that combines semantic vector distance, keyword frequency, and user learning-level compatibility. Rather than hallucinating episodes, the system parses live Apple iTunes feeds and real RSS XML show notes to ground our RAG engine and structured summaries. The frontend uses a distinctive 'Editorial Audio Intelligence' design language with multi-turn memory, personal bookmarking, and step-by-step learning journeys."*
