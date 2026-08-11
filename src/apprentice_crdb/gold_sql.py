"""Reference gold SQL for tests and the demo beat — NOT the frozen 50-question exam.

Claude authors eval/ independently. These queries must not be copied into the exam.
"""

from __future__ import annotations

# Naive day-0 attempt: calendar Q3, no soft-delete, no refunds, no cancel filter.
NAIVE_REVENUE_BY_REGION = """
SELECT r.name AS region, SUM(ol.amount_cents) AS revenue_cents
FROM order_lines ol
JOIN orders o ON o.order_id = ol.order_id
JOIN customers c ON c.customer_id = o.customer_id
JOIN regions r ON r.region_id = c.region_id
WHERE o.ordered_at >= '2026-07-01' AND o.ordered_at < '2026-10-01'
GROUP BY r.name
ORDER BY r.name
"""

# House-correct: fiscal Q3 (Aug–Oct), live orders only, net of refunds.
GOLD_REVENUE_BY_REGION = """
WITH live_orders AS (
    SELECT *
    FROM orders
    WHERE deleted_at IS NULL
      AND status != 'cancelled'
      AND ordered_at >= '2026-08-01'
      AND ordered_at < '2026-11-01'
),
gross AS (
    SELECT c.region_id, SUM(ol.amount_cents) AS gross_cents
    FROM order_lines ol
    JOIN live_orders o ON o.order_id = ol.order_id
    JOIN customers c ON c.customer_id = o.customer_id
    GROUP BY c.region_id
),
ref AS (
    SELECT c.region_id, SUM(rf.amount_cents) AS refund_cents
    FROM refunds rf
    JOIN live_orders o ON o.order_id = rf.order_id
    JOIN customers c ON c.customer_id = o.customer_id
    GROUP BY c.region_id
)
SELECT r.name AS region,
       COALESCE(g.gross_cents, 0) - COALESCE(f.refund_cents, 0) AS revenue_cents
FROM regions r
JOIN gross g ON g.region_id = r.region_id
LEFT JOIN ref f ON f.region_id = r.region_id
ORDER BY r.name
"""
