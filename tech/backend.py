from flask import Blueprint, request, jsonify, send_from_directory
from Wappalyzer import Wappalyzer, WebPage  
import os

tech_bp = Blueprint('tech_bp', __name__)

# Path to the folder where backend.py and index.html live
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Serve the HTML UI
@tech_bp.route("/", methods=["GET"])
def serve_ui():
    return send_from_directory(BASE_DIR, "index.html")

# POST endpoint for detecting technologies
@tech_bp.route("/", methods=["POST"])
def detect():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        wappalyzer = Wappalyzer.latest()
        webpage = WebPage.new_from_url(url)
        technologies = wappalyzer.analyze_with_categories(webpage)
        return jsonify(technologies)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
