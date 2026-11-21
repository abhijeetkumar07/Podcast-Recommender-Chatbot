from pydantic import BaseModel, Field
from typing import List, Optional

class QueryUnderstanding(BaseModel):
    topic: str = Field(description="Primary technical or conversational topic, e.g., 'Machine Learning'")
    subtopics: List[str] = Field(default_factory=list, description="Extracted subtopics or domains, e.g. ['Neural Networks', 'LLMs']")
    level: str = Field(default="All Levels", description="Target learning level: Beginner, Intermediate, Advanced, or All Levels")
    language: str = Field(default="English", description="Target language preference")
    duration_preference: str = Field(default="Any", description="Short (<30m), Medium (30-60m), Long (>60m), or Any")
    intent: str = Field(default="Recommendation", description="User intent: Recommendation, Search, Question, DeepDive, or LearningPath")

class PodcastRelevanceExplanation(BaseModel):
    podcast_id: str
    relevance_reason: str
    target_audience: str
    key_topics_covered: List[str]

class EpisodeSummaryStructure(BaseModel):
    short_overview: str
    detailed_explanation: str
    key_takeaways: List[str]
    important_concepts: List[str]
    practical_applications: List[str]
    beginner_explanation: str
    suggested_next_topics: List[str]
    grounding_source: str # "Full RSS Description" or "Transcript" or "Metadata"
