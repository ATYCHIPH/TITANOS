from __future__ import annotations

import os
from pathlib import Path
from .server.app import app, brain

# Compatibility layer for TITANOS-core
titanos = brain

def start_app(port: int = 8000, use_window: bool = False):
    import uvicorn
    import threading
    import time
    
    def run_server():
        print(f"TITANOS Operator starting on http://127.0.0.1:{port}")
        # Binding to 127.0.0.1 for maximum browser compatibility
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

    if use_window:
        try:
            import webview
            # Run server in background thread
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Wait a moment for server to start
            time.sleep(1.5)
            
            # Open native window
            print("Opening TITANOS Operator window...")
            webview.create_window(
                "TITANOS Operator", 
                f"http://127.0.0.1:{port}",
                width=1280, 
                height=800,
                background_color="#0a0a0a"
            )
            webview.start()
        except ImportError:
            print("pywebview not installed. Falling back to browser-only mode.")
            run_server()
    else:
        run_server()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--window", action="store_true")
    args = parser.parse_args()
    start_app(port=args.port, use_window=args.window)
