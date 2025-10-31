from flask import Blueprint, request, jsonify, send_from_directory
import requests
import os

subdomain_finder_bp = Blueprint('subdomain_finder_bp', __name__)

# Replace with your actual VirusTotal API key
API_KEY = "5aecaa8fb98b90257a9669756b65f4504338526e0f05603315f46b1758eb92d4"

@subdomain_finder_bp.route("/")
def home():
    """Serves the main index.html file."""
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

@subdomain_finder_bp.route("/", methods=["POST"])
def get_subdomains():
    """Receives a domain, fetches subdomains from VirusTotal, and returns them."""
    data = request.get_json()
    domain = data.get("domain")
    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    url = f"https://www.virustotal.com/vtapi/v2/domain/report?apikey={API_KEY}&domain={domain}"

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        res = r.json()

        subdomains_list = res.get("subdomains", [])
        formatted_results = [{"subdomain": s} for s in subdomains_list]

        return jsonify({"results": formatted_results})

    except requests.exceptions.HTTPError as http_err:
        return jsonify({"error": f"HTTP error occurred: {http_err}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
