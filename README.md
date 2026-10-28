# 迷你資料倉儲：零售銷售分析

以 DuckDB 與 Python 建置的小型資料倉儲練習專案。從正規化（3NF）的模擬交易資料出發，經過 ETL 轉成 star schema，再用 SQL 完成 OLAP 分析，並與 snowflake schema 做對照。

> 本專案使用的是程式產生的模擬資料，不含任何真實個資。

## 專案目標

1. 建立 1 張事實表與 4 張維度表的 star schema。
2. 撰寫可重複執行的 ETL 腳本，並以筆數與總金額驗證載入結果。
3. 用 SQL 實作 Roll-up、Drill-down、Slice、Dice、Pivot。
4. 將 DimProduct 改為 snowflake 結構，比較 JOIN 數、執行時間與儲存空間。

## 資料流程

```
模擬 OLTP 資料（CSV，3NF）
        ↓  Extract / Transform / Load（Python、pandas）
DuckDB 資料倉儲（star schema）
        ↓  SQL
OLAP 分析（Roll-up、Drill-down、Slice、Dice、Pivot）
```

## 資料夾結構

```
mini-dw/
├── README.md
├── requirements.txt
├── .gitignore
├── src/        generate_data.py、etl.py
├── sql/        schema_star.sql、schema_snowflake.sql、olap_queries.sql
├── docs/       er_star.png、er_snowflake.png、notes.md
├── data/       模擬 CSV（由腳本產生，不進版控）
└── warehouse.duckdb（由 ETL 產生，不進版控）
```

## 環境需求

- Python 3.10 以上
- 套件：`duckdb`、`pandas`

## 快速開始

```bash
# 1. 建立虛擬環境並安裝套件
python -m venv .venv
source .venv/bin/activate        # Windows：.venv\Scripts\activate
pip install -r requirements.txt

# 2. 產生模擬 OLTP 資料（輸出到 data/）
python src/generate_data.py

# 3. 執行 ETL，建立 warehouse.duckdb
python src/etl.py

# 4. 進入資料庫執行 OLAP 查詢
duckdb warehouse.duckdb
```

每次執行 `etl.py` 都會重建資料倉儲，可以放心重跑。

## 來源資料（OLTP，3NF）

| 資料表 | 主要欄位 | 預計筆數 |
| --- | --- | --- |
| Customers | CustomerID、Name、City | 500 |
| Products | ProductID、ProductName、Category、Brand、UnitPrice | 100 |
| Stores | StoreID、StoreName、City、Region | 10 |
| Orders | OrderID、OrderDate、CustomerID、StoreID | 20,000 |
| OrderDetails | OrderID、ProductID、Quantity | 60,000 |

分析期間為連續 2 年，筆數可依電腦效能調整。

## Star Schema

事實表的粒度為「一張訂單中的一個商品明細」。

| 資料表 | 類型 | 主要欄位 |
| --- | --- | --- |
| FactSales | 事實表 | DateKey、ProductKey、CustomerKey、StoreKey；Quantity、Amount |
| DimDate | 維度表 | DateKey、FullDate、Year、Quarter、Month、Week、DayOfWeek |
| DimProduct | 維度表 | ProductKey、ProductID、ProductName、Category、Brand、UnitPrice |
| DimCustomer | 維度表 | CustomerKey、CustomerID、Name、City |
| DimStore | 維度表 | StoreKey、StoreID、StoreName、City、Region |

## ETL 說明

1. **Extract**：用 pandas 讀入來源 CSV。
2. **Transform**：處理缺值與重複列、統一型別、產生 DimDate、建立代理鍵、計算 `Amount = Quantity × UnitPrice`。
3. **Load**：先載入維度表，再載入 FactSales。
4. **驗證**：核對來源與倉儲的筆數與總銷售金額，不一致就中止並報錯。

## OLAP 查詢範例

Roll-up：每年每月的銷售總額。

```sql
SELECT d.Year, d.Month, SUM(f.Amount) AS total_amount
FROM FactSales f
JOIN DimDate d ON f.DateKey = d.DateKey
GROUP BY d.Year, d.Month
ORDER BY d.Year, d.Month;
```

完整的 Roll-up、Drill-down、Slice、Dice、Pivot 查詢放在 `sql/olap_queries.sql`。

## Snowflake 對照實驗

將 DimProduct 拆成 Product、Category、Brand 三張正規化的表，其餘維度不變，用同一批資料重跑相同查詢，記錄以下項目：

| 比較項目 | Star | Snowflake |
| --- | --- | --- |
| 查詢的 JOIN 數 | 待實測 | 待實測 |
| 查詢執行時間 | 待實測 | 待實測 |
| 維度表儲存空間 | 待實測 | 待實測 |
| SQL 撰寫複雜度 | 待評估 | 待評估 |

結論整理在 `docs/notes.md`。

## 專案進度

- [ ] 產生模擬 OLTP 資料
- [ ] 建立 star schema
- [ ] 完成 ETL 與驗證
- [ ] 完成 5 種 OLAP 查詢
- [ ] 完成 snowflake 對照實驗
- [ ] 整理 ER 圖與筆記

## 注意事項

- `data/` 與 `warehouse.duckdb` 不進版控，請依「快速開始」自行重現。
- 請勿提交任何真實個資、密碼或金鑰。