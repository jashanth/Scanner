from flask import Blueprint, request, jsonify, send_from_directory
import requests
import re
import os
import time

js_bp = Blueprint('js_bp', __name__)

WAYBACK_URL = "https://web.archive.org/cdx/search/cdx"
JS_REGEX = re.compile(r'\.js($|\?)', re.IGNORECASE)

def fetch_wayback_urls(domain):
    params = {
        "url": f"*.{domain}/*",
        "collapse": "urlkey",
        "output": "text",
        "fl": "original",
        "limit": "10000"
    }
    max_retries = 5
    for attempt in range(max_retries):
        try:
            res = requests.get(WAYBACK_URL, params=params, timeout=(10, 120))
            res.raise_for_status()
            return res.text.splitlines()
        except requests.RequestException:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    return []

def filter_js_urls(urls):
    return [u for u in urls if JS_REGEX.search(u)]

@js_bp.route("/", methods=["GET"])
def serve_ui():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

@js_bp.route("/jsfinder", methods=["POST"])
def jsfinder():
    data = request.get_json()
    domain = data.get("domain", "").strip()
    if not domain:
        return jsonify({"error": "No domain provided"}), 400
    try:
        urls = fetch_wayback_urls(domain)
        js_urls = filter_js_urls(urls)
        return jsonify({"domain": domain, "count": len(js_urls), "urls": js_urls})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
