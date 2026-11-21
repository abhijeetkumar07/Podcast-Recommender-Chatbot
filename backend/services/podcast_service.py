import urllib.parse
import requests
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Any, Optional
from config import config

logger = logging.getLogger(__name__)

class PodcastService:
    ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
    ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"

    @classmethod
    def search_podcasts(cls, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Searches podcasts using the verified Apple iTunes Search API.
        Extracts genuine metadata: title, publisher, artwork, episode count, feedUrl, topics.
        """
        if not query:
            return []

        try:
            params = {
                "term": query,
                "media": "podcast",
                "entity": "podcast",
                "limit": min(limit, config.MAX_SEARCH_RESULTS)
            }
            logger.info(f"Querying iTunes API for term: '{query}'")
            resp = requests.get(cls.ITUNES_SEARCH_URL, params=params, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("results", []):
                genres = item.get("genres", [])
                primary_genre = genres[0] if genres else "General"
                
                podcast_id = str(item.get("collectionId", ""))
                title = item.get("collectionName", "Unknown Podcast")
                publisher = item.get("artistName", "Independent Creator")
                feed_url = item.get("feedUrl", "")
                external_url = item.get("collectionViewUrl", "#")
                artwork = item.get("artworkUrl600") or item.get("artworkUrl100", "")
                episodes = item.get("trackCount", 0)

                results.append({
                    "id": podcast_id,
                    "title": title,
                    "publisher": publisher,
                    "description": f"{title} hosted by {publisher}. Genre: {primary_genre}.",
                    "episodes": episodes,
                    "image_url": artwork,
                    "topics": genres if genres else ["General"],
                    "genre": primary_genre,
                    "external_url": external_url,
                    "feed_url": feed_url,
                    "source": "itunes"
                })

            return results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying iTunes search API: {e}")
            return []

    @classmethod
    def get_podcast_details(cls, podcast_id: str) -> Optional[Dict[str, Any]]:
        """
        Looks up detailed podcast metadata and recent real episodes from iTunes & RSS feed.
        """
        try:
            params = {"id": podcast_id, "entity": "podcast"}
            resp = requests.get(cls.ITUNES_LOOKUP_URL, params=params, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("results"):
                return None

            item = data["results"][0]
            feed_url = item.get("feedUrl", "")
            
            episodes = []
            podcast_full_desc = ""

            # Fetch real episode descriptions from genuine RSS feed if available
            if feed_url:
                try:
                    feed_resp = requests.get(feed_url, timeout=7, headers={"User-Agent": "PodcastGPT/2.0"})
                    if feed_resp.status_code == 200 and len(feed_resp.content) <= 10 * 1024 * 1024:
                        root = ET.fromstring(feed_resp.content)
                        channel = root.find("channel")
                        if channel is not None:
                            desc_elem = channel.find("description")
                            if desc_elem is not None and desc_elem.text:
                                podcast_full_desc = desc_elem.text.strip()

                            # Extract up to 10 latest episodes
                            for ep_item in channel.findall("item")[:10]:
                                ep_title = ep_item.findtext("title", "Episode")
                                ep_desc = ep_item.findtext("description", "")
                                pub_date = ep_item.findtext("pubDate", "")
                                link = ep_item.findtext("link", "")
                                duration = ep_item.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}duration", "")

                                episodes.append({
                                    "title": ep_title.strip() if ep_title else "Episode",
                                    "description": ep_desc.strip() if ep_desc else "No description provided.",
                                    "published_at": pub_date,
                                    "duration": duration,
                                    "link": link
                                })
                except Exception as feed_err:
                    logger.warning(f"Could not parse RSS feed {feed_url}: {feed_err}")

            return {
                "id": str(item.get("collectionId", "")),
                "title": item.get("collectionName", "Unknown Podcast"),
                "publisher": item.get("artistName", "Independent Creator"),
                "description": podcast_full_desc or f"Podcast by {item.get('artistName', '')}",
                "episodes_count": item.get("trackCount", len(episodes)),
                "image_url": item.get("artworkUrl600") or item.get("artworkUrl100", ""),
                "topics": item.get("genres", []),
                "genre": item.get("primaryGenreName", "General"),
                "external_url": item.get("collectionViewUrl", "#"),
                "feed_url": feed_url,
                "episodes": episodes
            }
        except Exception as e:
            logger.error(f"Error fetching details for podcast {podcast_id}: {e}")
            return None
