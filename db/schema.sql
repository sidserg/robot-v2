-- schema.sql — SQLite схема RobotV2

PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    robot_id INTEGER NOT NULL,
    ts TEXT NOT NULL,
    kind TEXT NOT NULL,
    ticker TEXT,
    figi TEXT,
    qty REAL,
    price REAL,
    total REAL,
    commission REAL DEFAULT 0.0,
    order_id TEXT,
    status TEXT,
    mode TEXT,
    strategy TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_trades_robot ON trades(robot_id);
CREATE INDEX IF NOT EXISTS idx_trades_ts ON trades(ts);
CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    robot_id INTEGER NOT NULL,
    figi TEXT,
    direction TEXT,
    qty REAL,
    price REAL,
    order_type TEXT,
    status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_orders_robot ON orders(robot_id);

CREATE TABLE IF NOT EXISTS robot_state (
    robot_id INTEGER PRIMARY KEY,
    running INTEGER DEFAULT 0,
    last_ts TEXT,
    day_date TEXT,
    day_equity_start REAL DEFAULT 0.0,
    day_stopped INTEGER DEFAULT 0,
    peak_value REAL DEFAULT 0.0,
    stop_order_id TEXT
);

INSERT OR IGNORE INTO schema_version(version) VALUES (1);