import ssl
import socket
from flask import Blueprint, request, jsonify, send_from_directory
from datetime import datetime
import os

ssl_bp = Blueprint('ssl_bp', __name__)

@ssl_bp.route("/", methods=["GET"])
def serve_ui():
    folder = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder, "index.html")

def flatten_name(entry):
    """Convert cert subject/issuer tuples into a flat dict."""
    result = {}
    for rdn in entry:
        for (key, value) in rdn:
            result[key] = value
    return result

@ssl_bp.route("/scan", methods=["POST"])
def tls_test():
    data = request.get_json()
    host = data.get("host", "").strip()
    if not host:
        return jsonify({"error": "Host required"}), 400

    if ":" in host:
        server, port = host.split(":")
        port = int(port)
    else:
        server, port = host, 443

    try:
        ctx = ssl.create_default_context()
        conn = ctx.wrap_socket(socket.socket(socket.AF_INET), server_hostname=server)
        conn.settimeout(5.0)
        conn.connect((server, port))

        cert = conn.getpeercert()
        cipher = conn.cipher() or ()
        protocol = conn.version() or "Unknown"
        conn.close()

        # Parse certificate validity dates
        not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z")
        not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days_left = (not_after - datetime.utcnow()).days

        # Handle cipher tuple safely
        cipher_name = cipher[0] if len(cipher) > 0 else "Unknown"
        cipher_protocol = cipher[1] if len(cipher) > 1 else "Unknown"
        cipher_bits = cipher[2] if len(cipher) > 2 else 0

        subject = flatten_name(cert.get("subject", []))
        issuer = flatten_name(cert.get("issuer", []))

        results = {
            "server": server,
            "port": port,
            "subject": subject,
            "issuer": issuer,
            "not_before": not_before.isoformat(),
            "not_after": not_after.isoformat(),
            "days_left": days_left,
            "protocol": protocol,
            "cipher": cipher_name,
            "cipher_protocol": cipher_protocol,
            "cipher_strength": cipher_bits,
        }
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
