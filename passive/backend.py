from flask import Blueprint, request, jsonify, send_from_directory
import requests
import os

passive_bp = Blueprint('passive_bp', __name__)

@passive_bp.route("/", methods=["GET"])
def serve_ui():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

@passive_bp.route("/search", methods=["POST"])
def passive_links():
    data = request.get_json()
    domain = data.get("domain")
    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    url = f"https://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=text&fl=original&collapse=urlkey&limit=8000"

    try:
        headers = {'User-Agent': 'PassiveLinkFinder/1.0'}
        r = requests.get(url, headers=headers, timeout=(10,120))
        r.raise_for_status()

        links = [x.strip() for x in r.text.split("\n") if x.strip()]
        return jsonify({"results": links})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch from Wayback: {e}"}), 500
