#!/usr/bin/env python3
"""Intentionally vulnerable FTP lab for isolated, authorized training only."""

import argparse
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PASSIVE_PORTS = range(6000, 6010)

DASHBOARD_HTML = """<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cyber-Bot FTP Lab</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    body { margin: 0; padding: 24px; background: #0b1220; color: #e2e8f0; }
    main { max-width: 850px; margin: auto; }
    section { margin: 0 0 18px; padding: 22px; border: 1px solid #29374d; border-radius: 14px; background: #131e30; }
    h1 { color: #4ade80; } h2 { color: #7dd3fc; }
    code, pre { direction: ltr; text-align: left; background: #09111e; border-radius: 7px; }
    code { padding: 2px 6px; } pre { overflow-x: auto; padding: 14px; white-space: pre-wrap; }
    .warning { color: #fbbf24; }
  </style>
</head>
<body><main>
  <section>
    <h1>🛡️ Cyber-Bot FTP Pentest Lab</h1>
    <p>لاب تدريبي محلي يحتوي على إعدادات FTP ضعيفة عمداً. اجمع أجزاء الـ Flag من الخدمة.</p>
    <p class="warning">⚠️ لا تفتحه على الإنترنت ولا تختبر أي جهاز خارج اللاب أو بدون إذن.</p>
  </section>
  <section>
    <h2>🎯 التحدي</h2>
    <ol>
      <li>افحص منفذ FTP واكتشف إعداد الدخول المجهول.</li>
      <li>ابحث عن ملف التلميح، ثم اختبر كلمة مرور ضعيفة لحساب التحدي باستخدام قائمة كلمات محلية.</li>
      <li>نزّل الأرشيف المحمي واختبر قوته محلياً باستخدام أدوات كالي.</li>
      <li>اجمع أجزاء الـ Flag الموجودة في ملفات FTP.</li>
    </ol>
  </section>
  <section>
    <h2>🔍 أمثلة كالي</h2>
    <pre>nmap -sV -p 2121 TARGET_IP
ftp TARGET_IP 2121
hydra -l ftpuser -P /path/to/wordlist.txt -s 2121 -f ftp://TARGET_IP
fcrackzip -u -D -p /path/to/wordlist.txt backup.zip
unzip backup.zip</pre>
    <p>استبدل <code>TARGET_IP</code> بعنوان الجهاز الذي شغّلت عليه اللاب، وليس عنواناً عاماً.</p>
  </section>
</main></body></html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        payload = DASHBOARD_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        sys.stdout.write("[HTTP] " + (fmt % args) + "\n")


def check_lab_files():
    required = (
        DATA_DIR / "public" / "welcome.txt",
        DATA_DIR / "public" / "flag_part1.txt",
        DATA_DIR / "public" / "hint.txt",
        DATA_DIR / "ftpuser" / "flag_part2.txt",
        DATA_DIR / "ftpuser" / "hint.txt",
        DATA_DIR / "ftpuser" / "backup.zip",
        DATA_DIR / "admin" / "flag_part3.txt",
    )
    missing = [str(path.relative_to(BASE_DIR)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing lab files: " + ", ".join(missing))


def start_http_dashboard(host, port):
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    server.daemon_threads = True
    print(f"[+] Web dashboard listening on {host}:{port}")
    server.serve_forever()


def start_ftp_server(host, port, advertise_address=None):
    try:
        from pyftpdlib.authorizers import DummyAuthorizer
        from pyftpdlib.handlers import FTPHandler
        from pyftpdlib.servers import FTPServer
    except ImportError as exc:
        raise RuntimeError("pyftpdlib is missing; install requirements.txt") from exc

    check_lab_files()
    authorizer = DummyAuthorizer()
    authorizer.add_anonymous(str(DATA_DIR / "public"), perm="elr")
    authorizer.add_user("ftpuser", "123456", str(DATA_DIR / "ftpuser"), perm="elrw")
    authorizer.add_user("admin", "admin123", str(DATA_DIR / "admin"), perm="elrw")

    class LabFTPHandler(FTPHandler):
        pass

    LabFTPHandler.authorizer = authorizer
    LabFTPHandler.banner = "Cyber-Bot FTP training lab - authorized practice only"
    LabFTPHandler.passive_ports = PASSIVE_PORTS
    if advertise_address:
        # Required behind Docker/NAT so PASV clients can reach the host's LAN IP.
        LabFTPHandler.masquerade_address = advertise_address

    server = FTPServer((host, port), LabFTPHandler)
    print(f"[+] FTP listening on {host}:{port}; passive TCP ports 6000-6009")
    server.serve_forever(timeout=1, blocking=True)


def main():
    parser = argparse.ArgumentParser(description="Isolated Cyber-Bot FTP training lab")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: loopback only)")
    parser.add_argument("--port", type=int, default=2121, help="FTP control port (default: 2121)")
    parser.add_argument("--http-port", type=int, default=8080, help="Dashboard port (default: 8080)")
    parser.add_argument(
        "--advertise-address",
        default=os.environ.get("LAB_ADVERTISE_ADDRESS"),
        help="Address returned to passive FTP clients behind NAT/Docker",
    )
    parser.add_argument("--no-http", action="store_true", help="Disable the optional dashboard")
    args = parser.parse_args()

    print("Cyber-Bot FTP Pentest Lab — intentionally vulnerable; private lab use only")
    if not args.no_http:
        dashboard = threading.Thread(
            target=start_http_dashboard,
            args=(args.host, args.http_port),
            daemon=True,
        )
        dashboard.start()

    try:
        start_ftp_server(args.host, args.port, args.advertise_address)
    except (OSError, RuntimeError, FileNotFoundError) as exc:
        print(f"[-] {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[*] Lab stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
