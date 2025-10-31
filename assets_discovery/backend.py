from flask import Blueprint, request, jsonify, send_from_directory
import requests
import os

assets_discovery_bp = Blueprint('assets_discovery_bp', __name__)

URLSCAN_API = "https://urlscan.io/api/v1/search/"

@assets_discovery_bp.route("/", methods=["GET"])
def serve_ui():
    # Serve index.html from the current folder of backend.py
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

@assets_discovery_bp.route("/urlscan-assets", methods=["POST"])
def urlscan_assets():
    data = request.get_json()
    domain = data.get("domain")
    if not domain:
        return jsonify({"error": "Domain required"}), 400

    try:
        query_url = f"{URLSCAN_API}?q=domain:{domain}&size=10"
        res = requests.get(query_url)
        res.raise_for_status()
        results = res.json().get("results", [])

        parsed = []
        for r in results:
            page = r.get("page", {})
            task = r.get("task", {})
            parsed.append({
                "domain": task.get("domain"),
                "ip": page.get("ip"),
                "asn": page.get("asn"),
                "asnname": page.get("asnname"),
                "server": page.get("server"),
                "country": page.get("country"),
                "title": page.get("title"),
                "tlsIssuer": page.get("tlsIssuer"),
                "tlsValidFrom": page.get("tlsValidFrom"),
                "screenshot": r.get("screenshot"),
                "result": r.get("result")
            })
        return jsonify({"results": parsed})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
