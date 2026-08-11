-- Deterministic seed. Amounts chosen so house-rule mistakes change the result set.

INSERT INTO regions (region_id, name) VALUES
    (1, 'AMER'),
    (2, 'EMEA'),
    (3, 'APAC');

INSERT INTO customers (customer_id, name, region_id) VALUES
    (1, 'Northwind Retail', 1),
    (2, 'Rhine Goods', 2),
    (3, 'Harbor Pacific', 3);

INSERT INTO products (product_id, sku, name, category) VALUES
    (1, 'WID-100', 'Widget', 'hardware'),
    (2, 'GAD-200', 'Gadget', 'hardware'),
    (3, 'SUB-300', 'Support plan', 'services');

-- Calendar vs fiscal (FY starts 1 Feb):
--   calendar Q3 2026 = Jul–Sep
--   fiscal   Q3 2026 = Aug–Oct
-- July-only and October-only rows make the two Q3 definitions disagree.

INSERT INTO orders (order_id, customer_id, ordered_at, deleted_at, status) VALUES
    -- calendar Q3 only (July) — fiscal Q2
    (10, 1, '2026-07-15', NULL, 'shipped'),
    -- both Q3 definitions (August)
    (20, 2, '2026-08-10', NULL, 'shipped'),
    -- calendar Q3, but SOFT-DELETED — naive SUM includes this
    (30, 3, '2026-09-05', '2026-09-06', 'shipped'),
    -- fiscal Q3 only (October) — calendar Q4
    (40, 1, '2026-10-12', NULL, 'shipped'),
    -- cancelled (not revenue)
    (50, 2, '2026-08-20', NULL, 'cancelled'),
    -- earlier FY (May = fiscal Q2) for YoY-ish questions
    (60, 3, '2026-05-03', NULL, 'shipped');

INSERT INTO order_lines (line_id, order_id, product_id, qty, amount_cents) VALUES
    (100, 10, 1, 10, 100000),   -- $1,000 July AMER
    (101, 20, 2, 4, 40000),     -- $400 August EMEA
    (102, 30, 1, 50, 500000),   -- $5,000 deleted September APAC
    (103, 40, 3, 1, 250000),    -- $2,500 October AMER services
    (104, 50, 2, 8, 80000),     -- cancelled
    (105, 60, 1, 2, 20000);     -- $200 May APAC

-- Refund on the July order so net ≠ gross for calendar Q3.
INSERT INTO refunds (refund_id, order_id, refunded_at, amount_cents) VALUES
    (1, 10, '2026-07-28', 25000);  -- $250 refund
