from datetime import datetime
import os
from typing import Optional

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, Header, HTTPException, Query, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


SERVICE_NAME = os.getenv("SERVICE_NAME", "access-gate")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "lab-token")

DB_REQUIRED = os.getenv("DB_REQUIRED", "false").lower() == "true"
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


app = FastAPI(
    title="Smart Campus — Access Gate Service",
    version="1.0.0",
    description="Access Gate service for FIT4110 Lab 05 Docker Compose deployment.",
)


# =========================================================
# In-memory fallback data
# Dùng khi chạy Lab 04 hoặc chạy local không bật DB_REQUIRED.
# Lab 05 khi DB_REQUIRED=true thì service sẽ kiểm tra DB trong /health.
# =========================================================

ACCESS_LOGS = [
    {
        "logType": "GRANTED",
        "logId": "log-001",
        "cardId": "card-001",
        "gateId": "gate-main",
        "direction": "IN",
        "timestamp": "2026-05-10T08:00:00Z",
        "status": "GRANTED",
        "personId": "SV001",
        "operatorNote": None,
        "grantedBy": "access-policy",
        "deniedReason": None,
        "accessMode": "RFID",
    },
    {
        "logType": "DENIED",
        "logId": "log-002",
        "cardId": "card-009",
        "gateId": "gate-main",
        "direction": "OUT",
        "timestamp": "2026-05-10T08:05:00Z",
        "status": "DENIED",
        "personId": None,
        "operatorNote": "The dang bi khoa",
        "grantedBy": None,
        "deniedReason": "CARD_BLOCKED",
        "accessMode": "RFID",
    },
]

GATES = {
    "gate-main": {
        "gateId": "gate-main",
        "gateName": "Cong chinh",
        "status": "ONLINE",
        "currentMode": "TWO_WAY",
        "lastUpdatedAt": "2026-05-10T08:00:00Z",
        "reason": None,
    },
    "gate-parking": {
        "gateId": "gate-parking",
        "gateName": "Cong nha xe",
        "status": "MAINTENANCE",
        "currentMode": "ENTRY_ONLY",
        "lastUpdatedAt": "2026-05-10T08:10:00Z",
        "reason": "Dang bao tri barrier chieu ra",
    },
}

CARDS = {
    "card-001": {
        "cardId": "card-001",
        "cardCode": "RFID-2026-001",
        "cardType": "RFID",
        "status": "ACTIVE",
        "issuedTo": "SV001",
        "validFrom": "2026-01-01",
        "validTo": "2026-12-31",
        "lastUsedAt": "2026-05-10T08:00:00Z",
        "note": None,
    },
    "card-009": {
        "cardId": "card-009",
        "cardCode": "RFID-2026-009",
        "cardType": "RFID",
        "status": "BLOCKED",
        "issuedTo": "SV009",
        "validFrom": "2026-01-01",
        "validTo": "2026-12-31",
        "lastUsedAt": "2026-05-09T17:30:00Z",
        "note": "The bi khoa do bao mat",
    },
}


# =========================================================
# ProblemDetails helpers
# =========================================================

def problem(status_code: int, title: str, detail: str, instance: str = ""):
    return {
        "type": "https://campus.local/errors/access-gate",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
        "correlationId": None,
        "errors": [],
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://campus.local/errors/validation",
            "title": "Validation Error",
            "status": 422,
            "detail": "Request validation failed",
            "instance": str(request.url.path),
            "correlationId": request.headers.get("X-Correlation-Id"),
            "errors": [
                {
                    "field": ".".join(str(part) for part in error.get("loc", [])),
                    "code": error.get("type", "VALIDATION_ERROR"),
                    "message": error.get("msg", "Invalid value"),
                }
                for error in exc.errors()
            ],
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "status" in exc.detail:
        content = exc.detail.copy()
        content["correlationId"] = request.headers.get("X-Correlation-Id")
        return JSONResponse(status_code=exc.status_code, content=content)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "https://campus.local/errors/access-gate",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": str(exc.detail),
            "instance": str(request.url.path),
            "correlationId": request.headers.get("X-Correlation-Id"),
            "errors": [],
        },
    )


# =========================================================
# Auth helpers
# =========================================================

def require_auth(authorization: Optional[str]) -> None:
    expected = f"Bearer {AUTH_TOKEN}"

    if not authorization or authorization.strip() != expected:
        raise HTTPException(
            status_code=401,
            detail=problem(
                401,
                "Unauthorized",
                "Missing or invalid Bearer token",
            ),
        )


# =========================================================
# Database helpers
# =========================================================

def validate_db_env():
    required = {
        "DB_HOST": DB_HOST,
        "DB_NAME": DB_NAME,
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
    }

    missing = [key for key, value in required.items() if not value]

    if DB_REQUIRED and missing:
        raise RuntimeError(
            f"Missing required database environment variables: {', '.join(missing)}"
        )


def get_conninfo() -> str:
    validate_db_env()

    return (
        f"host={DB_HOST} "
        f"port={DB_PORT} "
        f"dbname={DB_NAME} "
        f"user={DB_USER} "
        f"password={DB_PASSWORD} "
        f"connect_timeout=3"
    )


def check_db_connection():
    validate_db_env()

    if not DB_REQUIRED:
        return {
            "required": False,
            "status": "skipped",
        }

    with psycopg.connect(get_conninfo()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()

    return {
        "required": True,
        "status": "ok",
        "host": DB_HOST,
        "database": DB_NAME,
    }


def db_enabled() -> bool:
    return DB_REQUIRED


@app.on_event("startup")
def startup_validate_environment():
    validate_db_env()


# =========================================================
# Mapping DB rows to API response
# =========================================================

def map_card(row: dict):
    return {
        "cardId": row.get("card_id"),
        "cardCode": row.get("card_code"),
        "cardType": row.get("card_type"),
        "status": row.get("status"),
        "issuedTo": row.get("issued_to"),
        "validFrom": row.get("valid_from").isoformat() if row.get("valid_from") else None,
        "validTo": row.get("valid_to").isoformat() if row.get("valid_to") else None,
        "lastUsedAt": row.get("last_used_at").isoformat() if row.get("last_used_at") else None,
        "note": row.get("note"),
    }


def map_gate(row: dict):
    return {
        "gateId": row.get("gate_id"),
        "gateName": row.get("gate_name"),
        "status": row.get("status"),
        "currentMode": row.get("current_mode"),
        "lastUpdatedAt": row.get("last_updated_at").isoformat() if row.get("last_updated_at") else None,
        "reason": row.get("reason"),
    }


def map_access_log(row: dict):
    status = row.get("status")

    return {
        "logType": row.get("log_type"),
        "logId": row.get("log_id"),
        "cardId": row.get("card_id"),
        "gateId": row.get("gate_id"),
        "direction": row.get("direction"),
        "timestamp": row.get("timestamp").isoformat() if row.get("timestamp") else None,
        "status": status,
        "personId": row.get("person_id"),
        "operatorNote": row.get("operator_note"),
        "grantedBy": "access-policy" if status == "GRANTED" else None,
        "deniedReason": "CARD_BLOCKED" if status == "DENIED" else None,
        "accessMode": row.get("access_mode"),
    }


# =========================================================
# API endpoints
# =========================================================

@app.get("/health")
def health():
    try:
        db_status = check_db_connection()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=problem(
                503,
                "Service Unavailable",
                f"Database readiness check failed: {str(exc)}",
                "/health",
            ),
        )

    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "time": datetime.utcnow().isoformat() + "Z",
        "database": db_status,
    }


@app.get("/access/logs/recent")
def get_recent_access_logs(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-Id"),
    cursor: Optional[str] = Query(default=None, min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
    gateId: Optional[str] = Query(default=None),
    cardId: Optional[str] = Query(default=None),
    direction: Optional[str] = Query(default=None, pattern="^(IN|OUT)$"),
    status: Optional[str] = Query(default=None, pattern="^(GRANTED|DENIED|ERROR)$"),
    from_time: Optional[str] = Query(default=None, alias="from"),
    to_time: Optional[str] = Query(default=None, alias="to"),
):
    require_auth(authorization)

    if db_enabled():
        conditions = []
        params = []

        if gateId:
            conditions.append("gate_id = %s")
            params.append(gateId)

        if cardId:
            conditions.append("card_id = %s")
            params.append(cardId)

        if direction:
            conditions.append("direction = %s")
            params.append(direction)

        if status:
            conditions.append("status = %s")
            params.append(status)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        sql = f"""
            SELECT *
            FROM access_logs
            {where_clause}
            ORDER BY "timestamp" DESC
            LIMIT %s
        """

        params.append(limit)

        with psycopg.connect(get_conninfo(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        return {
            "items": [map_access_log(row) for row in rows],
            "nextCursor": None,
            "hasMore": False,
        }

    items = ACCESS_LOGS

    if gateId:
        items = [item for item in items if item["gateId"] == gateId]

    if cardId:
        items = [item for item in items if item["cardId"] == cardId]

    if direction:
        items = [item for item in items if item["direction"] == direction]

    if status:
        items = [item for item in items if item["status"] == status]

    return {
        "items": items[:limit],
        "nextCursor": None,
        "hasMore": False,
    }


@app.get("/access/logs/{logId}")
def get_access_log_by_id(
    logId: str = Path(..., pattern=r"^log-[a-zA-Z0-9-]{3,64}$"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-Id"),
):
    require_auth(authorization)

    if db_enabled():
        sql = "SELECT * FROM access_logs WHERE log_id = %s"

        with psycopg.connect(get_conninfo(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (logId,))
                row = cur.fetchone()

        if row:
            return map_access_log(row)

    else:
        for item in ACCESS_LOGS:
            if item["logId"] == logId:
                return item

    raise HTTPException(
        status_code=404,
        detail=problem(
            404,
            "Not Found",
            "Access log not found",
            f"/access/logs/{logId}",
        ),
    )


@app.get("/gates")
def list_gates(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-Id"),
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    require_auth(authorization)

    if db_enabled():
        sql = """
            SELECT *
            FROM gates
            ORDER BY gate_id
            LIMIT %s
        """

        with psycopg.connect(get_conninfo(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (limit,))
                rows = cur.fetchall()

        return {
            "items": [map_gate(row) for row in rows],
            "nextCursor": None,
            "hasMore": False,
        }

    return {
        "items": list(GATES.values())[:limit],
        "nextCursor": None,
        "hasMore": False,
    }


@app.get("/gates/{gateId}/status")
def get_gate_status(
    gateId: str = Path(..., pattern=r"^gate-[a-z0-9-]{2,40}$"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-Id"),
):
    require_auth(authorization)

    if db_enabled():
        sql = "SELECT * FROM gates WHERE gate_id = %s"

        with psycopg.connect(get_conninfo(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (gateId,))
                row = cur.fetchone()

        if row:
            return map_gate(row)

    else:
        gate = GATES.get(gateId)
        if gate:
            return gate

    raise HTTPException(
        status_code=404,
        detail=problem(
            404,
            "Not Found",
            "Gate not found",
            f"/gates/{gateId}/status",
        ),
    )


@app.get("/cards/{cardId}")
def get_card_by_id(
    cardId: str = Path(..., pattern=r"^card-[a-zA-Z0-9-]{3,64}$"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-Id"),
):
    require_auth(authorization)

    if db_enabled():
        sql = "SELECT * FROM access_cards WHERE card_id = %s"

        with psycopg.connect(get_conninfo(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (cardId,))
                row = cur.fetchone()

        if row:
            return map_card(row)

    else:
        card = CARDS.get(cardId)
        if card:
            return card

    raise HTTPException(
        status_code=404,
        detail=problem(
            404,
            "Not Found",
            "Card not found",
            f"/cards/{cardId}",
        ),
    )