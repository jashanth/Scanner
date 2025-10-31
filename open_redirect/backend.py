from flask import Blueprint, request, jsonify, send_from_directory
import requests
from requests.exceptions import RequestException
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

open_redirect_bp = Blueprint('open_redirect_bp', __name__)

# Payloads for open redirect testing
DEFAULT_PAYLOADS = [
    "//google.com",
    "//google.com/",
    "//google.com/%2f..",
    "///google.com/%2f..",
    "////google.com/%2f..",
    "/https://google.com",
    "https://google.com",
    "http://google.com",
    "/evil.com",
    "//evil.com",
    "https://evil.com",
    "/https/evil.com",
    "http:evil.com",
    "https:evil.com",
    "/?next=//evil.com",
    "/redirect?url=//evil.com"
]

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def is_external_redirect(base_url: str, location_header: str) -> bool:
    if not location_header:
        return False
    try:
        base_host = urlparse(base_url).hostname
        resolved_location = urljoin(base_url, location_header)
        location_host = urlparse(resolved_location).hostname
        if base_host and location_host and base_host.lower() != location_host.lower():
            return True
    except Exception:
        return False
    return False

def check_url(session: requests.Session, base_url: str, payload: str):
    test_url = base_url + payload
    result = {
        "payload": payload,
        "url": test_url,
        "status_code": None,
        "location": None,
        "status": "Error",
        "error": None
    }
    try:
        with session.get(
            test_url,
            timeout=8,
            allow_redirects=False,
            headers=REQUEST_HEADERS,
            verify=False
        ) as r:
            result["status_code"] = r.status_code
            location = r.headers.get("Location")
            result["location"] = location
            if 300 <= r.status_code < 400 and location:
                if is_external_redirect(test_url, location):
                    result["status"] = "Possible Vulnerability (External Redirect)"
                else:
                    result["status"] = "Safe (Internal Redirect)"
            else:
                result["status"] = "Safe (No Redirect)"
    except RequestException as e:
        result["error"] = f"Request Failed: {type(e).__name__}"
    except Exception as e:
        result["error"] = f"An unexpected error occurred: {str(e)}"
    return result

@open_redirect_bp.route("/", methods=["GET"])
def serve_ui():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

@open_redirect_bp.route("", methods=["POST"])
def open_redirect_scanner():
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    body = request.get_json()
    if not body or "url" not in body:
        return jsonify({"error": "Missing 'url' in request body"}), 400

    base_url = body["url"]
    if not base_url.startswith(('http://', 'https://')):
        return jsonify({"error": "URL must start with http:// or https://"}), 400
    if '=' not in urlparse(base_url).query:
        return jsonify({"error": "URL must contain a parameter for testing (e.g., ?redirect=)"}), 400

    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        with requests.Session() as session:
            future_to_payload = {
                executor.submit(check_url, session, base_url, payload): payload
                for payload in DEFAULT_PAYLOADS
            }
            for future in as_completed(future_to_payload):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    payload = future_to_payload[future]
                    results.append({
                        "payload": payload,
                        "url": base_url + payload,
                        "status": "Error",
                        "error": f"Task generation failed: {str(e)}"
                    })

    sorted_results = sorted(results, key=lambda x: 'Vulnerability' not in x['status'])
    return jsonify({"results": sorted_results})
