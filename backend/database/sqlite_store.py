import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from config import config

logger = logging.getLogger(__name__)

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # User Preferences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT PRIMARY KEY,
            interests TEXT,           -- JSON array
            preferred_topics TEXT,    -- JSON array
            learning_level TEXT DEFAULT 'Intermediate', -- Beginner, Intermediate, Advanced
            preferred_language TEXT DEFAULT 'English',
            preferred_duration TEXT DEFAULT 'Any',      -- Short (<30m), Medium (30-60m), Long (>60m)
            professional_goals TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Conversations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT DEFAULT 'New Discovery Session',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Conversation Messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,       -- user, assistant, system, tool
            content TEXT NOT NULL,
            metadata TEXT,            -- JSON metadata (references, structured tags, tools)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
        );
    """)

    # Saved Podcasts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_podcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            podcast_id TEXT NOT NULL,
            title TEXT NOT NULL,
            publisher TEXT,
            image_url TEXT,
            genre TEXT,
            external_url TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, podcast_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Learning Journeys
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_journeys (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            goal TEXT NOT NULL,
            stages TEXT NOT NULL,     -- JSON array of stages with recommended real podcasts
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # Learning Progress
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journey_id TEXT NOT NULL,
            stage_index INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            UNIQUE(journey_id, stage_index),
            FOREIGN KEY (journey_id) REFERENCES learning_journeys (id) ON DELETE CASCADE
        );
    """)

    # Recommendation Feedback
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendation_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            podcast_id TEXT NOT NULL,
            feedback_type TEXT NOT NULL, -- like, dislike, listened, dismissed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()
    logger.info("SQLite database schema verified and initialized.")

# Run init automatically on import
init_db()
