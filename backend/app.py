from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import urllib.parse

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def home():
    return "Welcome to the Podcast App!"

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        user_input = request.json.get('query', '').lower()
        logger.info(f"Received search query: {user_input}")

        if not user_input:
            return jsonify({"error": "Query not provided"}), 400
        
        # Search for podcasts using iTunes API (Free, no auth required!)
        encoded_query = urllib.parse.quote(user_input)
        url = f"https://itunes.apple.com/search?term={encoded_query}&media=podcast&limit=10"
        
        logger.debug(f"Making request to iTunes API: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Successfully received response from iTunes API")
        
        # Format the response to match the existing frontend expectations
        recommendations = []
        for show in data.get("results", []):
            try:
                # Extract primary genre as the topic
                genres = show.get('genres', [])
                topics = [genres[0]] if genres else ["Podcast"]
                
                podcast = {
                    'id': str(show.get('collectionId', '')),
                    'title': show.get('collectionName', 'Unknown Title'),
                    'description': show.get('collectionName', '') + " by " + show.get('artistName', ''), # iTunes search API often lacks full descriptions in base results
                    'publisher': show.get('artistName', 'Unknown Publisher'),
                    'episodes': show.get('trackCount', 0),
                    'image_url': show.get('artworkUrl600') or show.get('artworkUrl100'),
                    'topics': topics,
                    'external_url': show.get('collectionViewUrl', '#')
                }
                recommendations.append(podcast)
            except Exception as e:
                logger.error(f"Error parsing show: {str(e)}")

        logger.info(f"Returning {len(recommendations)} recommendations")
        return jsonify(recommendations)

    except requests.exceptions.RequestException as e:
        logger.error(f"iTunes API request failed: {str(e)}")
        return jsonify({"error": f"Failed to fetch podcasts: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error in recommend endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the app without SSL for local development
    app.run(debug=True, host='localhost', port=5000)
