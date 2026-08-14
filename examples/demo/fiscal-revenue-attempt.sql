-- Analyst's first attempt: assumes the calendar quarter, gross, no order hygiene.
SELECT COALESCE(SUM(ln.amount_cents), 0) AS revenue_cents
FROM order_lines ln
JOIN orders t ON t.order_id = ln.order_id
WHERE t.ordered_at >= '2026-04-01' AND t.ordered_at < '2026-07-01'
