from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import os
import requests
import base64
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Spotify API credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

if not CLIENT_ID or not CLIENT_SECRET:
    logger.error("Spotify API credentials not found in environment variables")
    raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables are required")

logger.info(f"Using Client ID: {CLIENT_ID[:5]}...")

def get_spotify_token():
    """Get Spotify API access token"""
    try:
        auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        logger.debug("Requesting Spotify token...")
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token = response.json()["access_token"]
        logger.info("Successfully obtained Spotify token")
        return token
    except Exception as e:
        logger.error(f"Error getting Spotify token: {str(e)}")
        raise

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

        # Get Spotify access token
        token = get_spotify_token()
        
        # Search for podcasts using Spotify API
        url = "https://api.spotify.com/v1/search"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "q": user_input,
            "type": "show",
            "market": "US",
            "limit": 10
        }
        
        logger.debug(f"Making request to Spotify API with params: {params}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Successfully received response from Spotify API")
        
        # Format the response
        recommendations = []
        for show in data.get("shows", {}).get("items", []):
            podcast = {
                'id': show['id'],
                'title': show['name'],
                'description': show['description'],
                'publisher': show['publisher'],
                'episodes': show['total_episodes'],
                'image_url': show['images'][0]['url'] if show['images'] else None,
                'topics': [show['description'].split()[0]],  # Simple topic extraction
                'external_url': show['external_urls']['spotify']
            }
            recommendations.append(podcast)

        logger.info(f"Returning {len(recommendations)} recommendations")
        return jsonify(recommendations)
    except requests.exceptions.RequestException as e:
        logger.error(f"Spotify API request failed: {str(e)}")
        return jsonify({"error": f"Failed to fetch podcasts from Spotify: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error in recommend endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the app without SSL for local development
    app.run(debug=True, host='localhost', port=5000)
