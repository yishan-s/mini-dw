-- 1. Roll-up：由月往上彙總到年與總計
-- 月份欄位為 NULL 的列是該年小計，兩欄都是 NULL 的列是全部總計
SELECT d.Year, d.Month, SUM(f.Amount) AS total_amount
FROM FactSales f
JOIN DimDate d ON f.DateKey = d.DateKey
GROUP BY ROLLUP (d.Year, d.Month)
ORDER BY d.Year, d.Month;

-- 2. Drill-down：由月往下展開到日（以 2025 年 3 月為例）
SELECT d.FullDate, SUM(f.Amount) AS total_amount
FROM FactSales f
JOIN DimDate d ON f.DateKey = d.DateKey
WHERE d.Year = 2025 AND d.Month = 3
GROUP BY d.FullDate
ORDER BY d.FullDate;

-- 3. Slice：固定一個維度（年份 = 2025），其餘維度照常分析
SELECT p.Category, SUM(f.Amount) AS total_amount
FROM FactSales f
JOIN DimDate d ON f.DateKey = d.DateKey
JOIN DimProduct p ON f.ProductKey = p.ProductKey
WHERE d.Year = 2025
GROUP BY p.Category
ORDER BY total_amount DESC;

-- 4. Dice：同時固定多個維度（2025 年、北部與中部、飲料與零食）
SELECT s.Region, p.Category, SUM(f.Amount) AS total_amount
FROM FactSales f
JOIN DimDate d ON f.DateKey = d.DateKey
JOIN DimProduct p ON f.ProductKey = p.ProductKey
JOIN DimStore s ON f.StoreKey = s.StoreKey
WHERE d.Year = 2025
  AND s.Region IN ('北部', '中部')
  AND p.Category IN ('飲料', '零食')
GROUP BY s.Region, p.Category
ORDER BY s.Region, p.Category;

-- 5. Pivot：商品類別當列、季度當欄（2025 年）
SELECT p.Category,
       SUM(CASE WHEN d.Quarter = 1 THEN f.Amount ELSE 0 END) AS Q1,
       SUM(CASE WHEN d.Quarter = 2 THEN f.Amount ELSE 0 END) AS Q2,
       SUM(CASE WHEN d.Quarter = 3 THEN f.Amount ELSE 0 END) AS Q3,
       SUM(CASE WHEN d.Quarter = 4 THEN f.Amount ELSE 0 END) AS Q4
FROM FactSales f
JOIN DimDate d ON f.DateKey = d.DateKey
JOIN DimProduct p ON f.ProductKey = p.ProductKey
WHERE d.Year = 2025
GROUP BY p.Category
ORDER BY p.Category;