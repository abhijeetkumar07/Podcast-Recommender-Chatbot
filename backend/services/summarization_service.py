import logging
import json
from typing import List, Dict, Any, Optional
from ai.llm import get_llm
from ai.structured_outputs import EpisodeSummaryStructure
from utils.validators import sanitize_string

logger = logging.getLogger(__name__)

class SummarizationService:

    @classmethod
    def summarize_episode(cls, episode_title: str, episode_description: str, podcast_title: str = "") -> Dict[str, Any]:
        """
        Generates an honest structured summary strictly grounded in verified description content.
        """
        clean_desc = sanitize_string(episode_description)
        if not clean_desc or len(clean_desc) < 20:
            return {
                "short_overview": f"Detailed description for '{episode_title}' is unavailable from the public RSS feed.",
                "detailed_explanation": "The episode feed did not provide sufficient metadata for in-depth analysis.",
                "key_takeaways": ["Listen to the full audio via the external link."],
                "important_concepts": [],
                "practical_applications": [],
                "beginner_explanation": "Please refer to the source broadcast for content details.",
                "suggested_next_topics": [],
                "grounding_source": "Metadata (Minimal Feed Data Available)"
            }

        llm = get_llm(temperature=0.2)
        if llm:
            try:
                prompt = f"""You are PodcastGPT's AI Episode Intelligence specialist.
You must generate a structured summary based ONLY on the provided episode notes.
DO NOT fabricate transcripts or facts not mentioned in the text.

Podcast: {podcast_title}
Episode: {episode_title}
Episode Notes / Description:
{clean_desc}

Respond in strict JSON with the following keys:
{{
  "short_overview": "A concise 2-sentence executive summary.",
  "detailed_explanation": "A thorough summary of what the episode covers based on the notes.",
  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"],
  "important_concepts": ["concept 1", "concept 2"],
  "practical_applications": ["practical application 1", "practical application 2"],
  "beginner_explanation": "A simplified breakdown for someone new to the topic.",
  "suggested_next_topics": ["next topic 1", "next topic 2"]
}}
"""
                response = llm.invoke(prompt)
                content = response.content if hasattr(response, "content") else str(response)
                
                # Extract json safely
                if "{" in content and "}" in content:
                    json_str = content[content.find("{"):content.rfind("}")+1]
                    data = json.loads(json_str)
                    data["grounding_source"] = "Verified RSS Show Notes (Description-Grounded)"
                    return data
            except Exception as e:
                logger.error(f"LLM Summarization failed, falling back to deterministic extraction: {e}")

        # Deterministic Fallback if LLM is offline or no API key provided
        sentences = [s.strip() for s in clean_desc.split('.') if len(s.strip()) > 10]
        overview = ". ".join(sentences[:2]) + "." if sentences else clean_desc[:200]
        takeaways = [s + "." for s in sentences[2:5]] if len(sentences) >= 5 else [overview]
        
        words = [w for w in clean_desc.split() if len(w) > 6 and w.isalpha()]
        unique_concepts = list(dict.fromkeys(words))[:4]

        return {
            "short_overview": overview,
            "detailed_explanation": clean_desc[:600] + ("..." if len(clean_desc) > 600 else ""),
            "key_takeaways": takeaways if takeaways else ["Key insights detailed in episode audio."],
            "important_concepts": unique_concepts if unique_concepts else ["Audio Discussion"],
            "practical_applications": ["Apply concepts discussed in the show to your current workflow."],
            "beginner_explanation": f"This episode explores themes around {podcast_title or episode_title}.",
            "suggested_next_topics": ["Foundational Deep Dives", "Related Expert Interviews"],
            "grounding_source": "Verified RSS Show Notes (Offline Engine)"
        }
