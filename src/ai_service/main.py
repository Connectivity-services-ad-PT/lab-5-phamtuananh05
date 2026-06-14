from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone
import json


SERVICE_NAME = "access-gate-ai-service"
SERVICE_VERSION = "0.5.0"


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": SERVICE_NAME,
                    "version": SERVICE_VERSION,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            return

        self._send_json(
            404,
            {
                "type": "https://campus.local/errors/not-found",
                "title": "Not Found",
                "status": 404,
                "detail": "Endpoint not found",
            },
        )

    def do_POST(self) -> None:
        if self.path == "/predict":
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"

            try:
                request_body = json.loads(raw_body)
            except json.JSONDecodeError:
                request_body = {}

            card_id = request_body.get("cardId", "unknown")
            gate_id = request_body.get("gateId", "unknown")
            direction = request_body.get("direction", "IN")

            risk_level = "LOW"
            recommendation = "ALLOW_REVIEW"
            confidence = 0.91

            if card_id in ["card-009", "blocked-card", "unknown"]:
                risk_level = "HIGH"
                recommendation = "DENY"
                confidence = 0.97

            self._send_json(
                200,
                {
                    "service": SERVICE_NAME,
                    "version": SERVICE_VERSION,
                    "riskLevel": risk_level,
                    "recommendation": recommendation,
                    "confidence": confidence,
                    "cardId": card_id,
                    "gateId": gate_id,
                    "direction": direction,
                    "modelVersion": "mock-access-risk-v1",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            return

        self._send_json(
            404,
            {
                "type": "https://campus.local/errors/not-found",
                "title": "Not Found",
                "status": 404,
                "detail": "Endpoint not found",
            },
        )

    def log_message(self, format: str, *args) -> None:
        print("%s - - %s" % (self.address_string(), format % args))


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9000), Handler)
    print(f"{SERVICE_NAME} running on port 9000")
    server.serve_forever()