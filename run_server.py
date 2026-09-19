import os
import sys
import time
import threading
import webbrowser
import logging

# Ensure UTF-8 output protection on Windows
if sys.platform.startswith("win") and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import settings
from app import app

def open_browser(url: str, delay: float = 1.2):
    """
    Waits briefly for the Flask dev server to bind to the socket,
    then automatically opens the user's default web browser.
    """
    time.sleep(delay)
    print(f"\n[🚀] Opening web browser at: {url}\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[!] Could not launch default browser automatically: {e}")

def print_banner(host: str, port: int, url: str):
    banner = f"""
================================================================================
    ⚡ DevOps Autopilot – Infra Waste Resolver (Agentic AI) ⚡
================================================================================
  [✔] Backend API & Frontend Dashboard Unified Server
  [✔] Host: {host}  |  Port: {port}
  [✔] Web Dashboard: {url}
  [✔] REST API Endpoints:
      • POST {url}/api/optimize  (Trigger optimization run)
      • GET  {url}/api/savings   (Aggregate INR savings)
      • GET  {url}/api/runs      (List runs)
      • GET  {url}/health        (Health & guardrails status)
  [✔] Guardrails: Staging / Dev / Demo only | 50% max scale-down
================================================================================
  Press Ctrl+C to stop the server anytime.
================================================================================
"""
    print(banner)

import socket

def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def main():
    host = "127.0.0.1"
    port = settings.PORT
    url = f"http://{host}:{port}"

    print_banner(host, port, url)

    # If port is already in use by a running instance, launch browser and exit cleanly
    if is_port_in_use(host, port):
        print(f"[✔] DevOps Autopilot is already active and running on port {port}.")
        open_browser(url, delay=0.2)
        print("To stop the running instance, close the background terminal or use Ctrl+C.")
        return

    # Launch browser launch thread
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # Start Flask server
    try:
        app.run(host=host, port=port, debug=False, use_reloader=False)
    except OSError as e:
        if getattr(e, "winerror", None) == 10048 or "address already in use" in str(e).lower():
            print(f"\n[✔] Active DevOps Autopilot server detected on port {port}.")
            open_browser(url, delay=0.2)
        else:
            print(f"[!] Server startup error: {e}")
    except KeyboardInterrupt:
        print("\n[✔] DevOps Autopilot server stopped cleanly. Goodbye!\n")

if __name__ == "__main__":
    main()
