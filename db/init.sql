CREATE TABLE IF NOT EXISTS access_cards (
    card_id VARCHAR(80) PRIMARY KEY,
    card_code VARCHAR(80) NOT NULL,
    card_type VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL,
    issued_to VARCHAR(80),
    valid_from DATE,
    valid_to DATE,
    last_used_at TIMESTAMPTZ,
    note TEXT
);

CREATE TABLE IF NOT EXISTS gates (
    gate_id VARCHAR(80) PRIMARY KEY,
    gate_name VARCHAR(120) NOT NULL,
    status VARCHAR(30) NOT NULL,
    current_mode VARCHAR(30) NOT NULL,
    last_updated_at TIMESTAMPTZ,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS access_logs (
    log_id VARCHAR(80) PRIMARY KEY,
    log_type VARCHAR(30) NOT NULL,
    card_id VARCHAR(80),
    gate_id VARCHAR(80),
    direction VARCHAR(10) NOT NULL,
    status VARCHAR(30) NOT NULL,
    person_id VARCHAR(80),
    timestamp TIMESTAMPTZ NOT NULL,
    operator_note TEXT,
    access_mode VARCHAR(30)
);

INSERT INTO access_cards (
    card_id, card_code, card_type, status, issued_to, valid_from, valid_to, last_used_at, note
)
VALUES
    ('card-001', 'RFID-2026-001', 'RFID', 'ACTIVE', 'SV001', '2026-01-01', '2026-12-31', '2026-05-10T08:00:00Z', NULL),
    ('card-009', 'RFID-2026-009', 'RFID', 'BLOCKED', 'SV009', '2026-01-01', '2026-12-31', '2026-05-09T17:30:00Z', 'The bi khoa do bao mat')
ON CONFLICT (card_id) DO NOTHING;

INSERT INTO gates (
    gate_id, gate_name, status, current_mode, last_updated_at, reason
)
VALUES
    ('gate-main', 'Cong chinh', 'ONLINE', 'TWO_WAY', '2026-05-10T08:00:00Z', NULL),
    ('gate-parking', 'Cong nha xe', 'MAINTENANCE', 'ENTRY_ONLY', '2026-05-10T08:10:00Z', 'Dang bao tri barrier chieu ra')
ON CONFLICT (gate_id) DO NOTHING;

INSERT INTO access_logs (
    log_id, log_type, card_id, gate_id, direction, status, person_id, timestamp, operator_note, access_mode
)
VALUES
    ('log-001', 'GRANTED', 'card-001', 'gate-main', 'IN', 'GRANTED', 'SV001', '2026-05-10T08:00:00Z', NULL, 'RFID'),
    ('log-002', 'DENIED', 'card-009', 'gate-main', 'OUT', 'DENIED', NULL, '2026-05-10T08:05:00Z', 'The dang bi khoa', 'RFID')
ON CONFLICT (log_id) DO NOTHING;