-- DEMO FIXTURE: invented data and names, for skill trials only.
-- Top 3 customers by sales in each region, per month.
-- Copied from a forum answer. It works; not sure why.
SELECT *
FROM (
  SELECT region, customer_name, month, total_sales,
         ROW_NUMBER() OVER (PARTITION BY region, month ORDER BY total_sales DESC) AS rn
  FROM monthly_sales
) ranked
WHERE rn <= 3
ORDER BY region, month, rn;
