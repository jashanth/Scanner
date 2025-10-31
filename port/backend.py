from flask import Blueprint, request, jsonify, send_from_directory
import socket
import os

port_bp = Blueprint('port_bp', __name__)

@port_bp.route("/", methods=["GET"])
def serve_ui():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(folder_path, "index.html")

def scan_port(ip, port, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        if result == 0:
            try:
                sock.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                banner = sock.recv(1024).decode(errors="ignore").strip()
            except Exception:
                banner = ""
            finally:
                sock.close()
            return {"port": port, "status": "open", "banner": banner}
        else:
            sock.close()
            return {"port": port, "status": "closed", "banner": ""}
    except Exception as e:
        return {"port": port, "status": "error", "banner": str(e)}

@port_bp.route("/scan", methods=["POST"])
def port_scan():
    data = request.get_json()
    target = data.get("target", "").strip()
    ports_input = data.get("ports", "80,443")
    timeout = float(data.get("timeout", 1))

    if not target:
        return jsonify({"error": "Target is required"}), 400

    try:
        ip = socket.gethostbyname(target)
    except Exception:
        return jsonify({"error": "Could not resolve target"}), 400

    ports = []
    for part in ports_input.split(","):
        if "-" in part:
            start, end = part.split("-")
            ports.extend(range(int(start), int(end) + 1))
        else:
            try:
                ports.append(int(part))
            except:
                pass
    ports = sorted(set([p for p in ports if 1 <= p <= 65535]))

    results = [scan_port(ip, port, timeout) for port in ports]
    open_ports = [r for r in results if r["status"] == "open"]

    return jsonify({
        "target": target,
        "ip": ip,
        "ports_scanned": len(ports),
        "open_ports": len(open_ports),
        "results": results
    })
