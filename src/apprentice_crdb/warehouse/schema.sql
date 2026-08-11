-- Demo warehouse (SQLite prop). House semantics are NOT encoded as views
-- the naive agent would automatically use — they live in agent memory after corrections.

CREATE TABLE regions (
    region_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region_id INTEGER NOT NULL REFERENCES regions (region_id)
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    ordered_at TEXT NOT NULL,
    deleted_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('placed', 'shipped', 'cancelled'))
);

CREATE TABLE order_lines (
    line_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders (order_id),
    product_id INTEGER NOT NULL REFERENCES products (product_id),
    qty INTEGER NOT NULL,
    amount_cents INTEGER NOT NULL
);

CREATE TABLE refunds (
    refund_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders (order_id),
    refunded_at TEXT NOT NULL,
    amount_cents INTEGER NOT NULL
);
