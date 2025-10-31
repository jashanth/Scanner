from flask import Blueprint, request, jsonify, send_from_directory
import requests
import re
import os
import time

filefetcher_bp = Blueprint('filefetcher_bp', __name__)

WAYBACK_URL = "https://web.archive.org/cdx/search/cdx"
FILE_EXTENSIONS = r'\.(xls|xml|xlsx|json|pdf|sql|doc|docx|pptx|txt|zip|tar\.gz|tgz|bak|7z|rar|log|cache|secret|db|backup|yml|gz|config|csv|yaml|md|md5|exe|dll|bin|ini|bat|sh|tar|deb|rpm|iso|img|apk|msi|dmg|tmp|crt|pem|key|pub|asc)'

def fetch_wayback_urls(domain):
    params = {
        "url": f"*.{domain}/*",
        "collapse": "urlkey",
        "output": "text",
        "fl": "original",
        "limit": "8000"
    }
    for attempt in range(3):
        try:
            res = requests.get(WAYBACK_URL, params=params, timeout=(10,120))
            res.raise_for_status()
            return res.text.splitlines()
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff delay
    return []

def filter_urls_by_filetype(urls):
    return [u for u in urls if re.search(FILE_EXTENSIONS, u, re.IGNORECASE)]

@filefetcher_bp.route("/", methods=["GET"])
def serve_ui():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

@filefetcher_bp.route("/filefetcher", methods=["POST"])
def filefetcher():
    data = request.get_json()
    domain = data.get("domain", "").strip()
    if not domain:
        return jsonify({"error": "No domain provided"}), 400

    try:
        urls = fetch_wayback_urls(domain)
        filtered = filter_urls_by_filetype(urls)
        return jsonify({
            "domain": domain,
            "count": len(filtered),
            "urls": filtered
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
