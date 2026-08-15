SELECT COALESCE(SUM(li.amount_cents), 0) AS gross_cents
FROM order_lines li
JOIN orders od ON od.order_id = li.order_id
WHERE od.deleted_at IS NULL
  AND od.status <> 'cancelled'
  AND od.ordered_at >= '2026-01-01'
  AND od.ordered_at < '2027-01-01'
  AND li.product_id IN (
    SELECT pr.product_id
    FROM products pr
    WHERE pr.category = 'hardware'
  );
