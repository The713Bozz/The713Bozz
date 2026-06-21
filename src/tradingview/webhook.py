"""
TradingView webhook receiver.

TradingView Pine Script alerts can POST JSON to any publicly reachable URL.
This module provides:
  - parse_alert(): validate and parse an incoming alert body
  - WebhookServer: lightweight HTTP server to receive those alerts

Typical Pine Script alert JSON (configure in TradingView alert dialog → Webhook URL):
  {
    "symbol":    "{{ticker}}",
    "action":    "buy",          // or "sell" / "close"
    "price":     {{close}},
    "change":    {{change}},
    "volume":    {{volume}},
    "strategy":  "momentum_compounder",
    "secret":    "YOUR_WEBHOOK_SECRET"
  }

Set TV_WEBHOOK_SECRET in .env to validate that alerts come from TradingView.
Set TV_WEBHOOK_PORT (default 8765) to choose the listening port.
"""

import hashlib
import hmac
import json
import os
import queue
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Optional


@dataclass
class TVAlert:
    symbol: str
    action: str  # "buy" | "sell" | "close"
    price: float
    change: float = 0.0
    volume: float = 0.0
    strategy: str = ""
    interval: str = ""
    extra: dict = field(default_factory=dict)


class AlertParseError(Exception):
    pass


def parse_alert(body: bytes | str, secret: str = "") -> TVAlert:
    """
    Parse and validate a raw TradingView webhook payload.
    Raises AlertParseError on invalid input.
    """
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")

    body = body.strip()
    if not body:
        raise AlertParseError("Empty alert body.")

    try:
        data: dict = json.loads(body)
    except json.JSONDecodeError as exc:
        raise AlertParseError(f"Invalid JSON: {exc}") from exc

    # Secret validation (HMAC-SHA256 or plain string match)
    if secret:
        incoming_secret = data.get("secret", "")
        if not _validate_secret(incoming_secret, secret):
            raise AlertParseError("Webhook secret mismatch — alert rejected.")

    symbol = str(data.get("symbol") or data.get("ticker") or "").upper().strip()
    if not symbol:
        raise AlertParseError("Alert missing 'symbol' field.")

    action = str(data.get("action") or data.get("side") or "").lower().strip()
    if action not in ("buy", "sell", "close", "long", "short"):
        raise AlertParseError(f"Unknown alert action: {action!r}")
    if action == "long":
        action = "buy"
    if action == "short":
        action = "sell"

    try:
        price = float(data.get("price") or data.get("close") or 0)
    except (TypeError, ValueError):
        price = 0.0

    try:
        change = float(data.get("change") or 0)
    except (TypeError, ValueError):
        change = 0.0

    try:
        volume = float(data.get("volume") or 0)
    except (TypeError, ValueError):
        volume = 0.0

    known = {"symbol", "ticker", "action", "side", "price", "close",
             "change", "volume", "strategy", "interval", "secret"}
    extra = {k: v for k, v in data.items() if k not in known}

    return TVAlert(
        symbol=symbol,
        action=action,
        price=price,
        change=change / 100.0 if abs(change) > 1 else change,
        volume=volume,
        strategy=str(data.get("strategy") or ""),
        interval=str(data.get("interval") or ""),
        extra=extra,
    )


def _validate_secret(incoming: str, expected: str) -> bool:
    return hmac.compare_digest(
        incoming.encode("utf-8"),
        expected.encode("utf-8"),
    )


class WebhookServer:
    """
    Lightweight HTTP server that listens for TradingView alerts.

    Usage:
        server = WebhookServer(on_alert=my_handler)
        server.start()   # non-blocking, runs in a background thread
        # ... later ...
        server.stop()

    Or drain the built-in queue:
        server = WebhookServer()
        server.start()
        alert = server.queue.get()
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: Optional[int] = None,
        secret: str = "",
        on_alert: Optional[Callable[[TVAlert], None]] = None,
        path: str = "/webhook",
    ):
        self.host = host
        self.port = port or int(os.environ.get("TV_WEBHOOK_PORT", "8765"))
        self.secret = secret or os.environ.get("TV_WEBHOOK_SECRET", "")
        self.path = path
        self.on_alert = on_alert
        self.queue: queue.Queue[TVAlert] = queue.Queue()
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        server_ref = self

        class _Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):  # silence default access log
                pass

            def do_POST(self):
                if self.path != server_ref.path:
                    self.send_response(404)
                    self.end_headers()
                    return

                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b""
                try:
                    alert = parse_alert(body, secret=server_ref.secret)
                except AlertParseError as exc:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(f"Bad request: {exc}".encode())
                    return

                server_ref.queue.put(alert)
                if server_ref.on_alert:
                    try:
                        server_ref.on_alert(alert)
                    except Exception:
                        pass

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")

            def do_GET(self):
                if self.path in (server_ref.path, "/health"):
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"The713Bozz TradingView webhook ready")
                else:
                    self.send_response(404)
                    self.end_headers()

        self._server = HTTPServer((self.host, self.port), _Handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True, name="tv-webhook"
        )
        self._thread.start()
        print(
            f"[TV Webhook] Listening on http://{self.host}:{self.port}{self.path}"
        )

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None
