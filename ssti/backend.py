from flask import Blueprint, request, jsonify, send_from_directory
import requests
import os

ssti_bp = Blueprint('ssti_bp', __name__)

PAYLOADS = [
    ("{{7*7}}", "49"),
    ("{{9*9}}", "81"),
    ("{{1337*1337}}", str(1337*1337)),
    ("${{7*7}}", "49"),
    ("<%= 7*7 %>", "49"),
    ("${7*7}", "49")
]

@ssti_bp.route("/", methods=["GET"])
def serve_ui():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

@ssti_bp.route("/api", methods=["POST"])
def ssti_test():
    data = request.get_json()
    base_url = data.get("url")
    if not base_url or "?" not in base_url:
        return jsonify({"error": "URL must include ?param= structure"}), 400

    results = []
    for payload, expected in PAYLOADS:
        test_url = base_url + payload
        try:
            r = requests.get(test_url, timeout=10, verify=False)
            match = expected in r.text
            results.append({
                "payload": payload,
                "expected": expected,
                "url": test_url,
                "status_code": r.status_code,
                "vulnerable": match
            })
        except Exception as e:
            results.append({
                "payload": payload,
                "expected": expected,
                "url": test_url,
                "status_code": "error",
                "vulnerable": False,
                "error": str(e)
            })

    return jsonify({"results": results})
