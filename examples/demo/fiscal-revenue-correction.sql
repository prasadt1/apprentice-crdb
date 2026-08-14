-- House-correct: fiscal Q2 is May-July (FY starts 1 Feb); live, non-cancelled; net of refunds.
WITH keep2 AS (
  SELECT t.order_id
  FROM orders t
  WHERE t.deleted_at IS NULL
    AND t.status <> 'cancelled'
    AND t.ordered_at >= '2026-05-01'
    AND t.ordered_at < '2026-08-01'
)
SELECT COALESCE(SUM(ln.amount_cents), 0)
     - COALESCE((SELECT SUM(rf2.amount_cents) FROM refunds rf2
                 WHERE rf2.order_id IN (SELECT k.order_id FROM keep2 k)), 0) AS revenue_cents
FROM order_lines ln
JOIN keep2 ON keep2.order_id = ln.order_id
