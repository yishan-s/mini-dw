"""Snowflake 對照實驗：把 star schema 的 DimProduct 拆成三張表，並與原本的 star 比較。

執行方式（在專案根目錄，需先跑過 etl.py）：
    python src/snowflake_experiment.py

會產生 warehouse_snowflake.duckdb（已被 .gitignore 排除），並印出比較結果。
"""

import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
STAR_PATH = ROOT / "warehouse.duckdb"
SNOW_PATH = ROOT / "warehouse_snowflake.duckdb"
SCHEMA_FILE = ROOT / "sql" / "schema_snowflake.sql"
RUNS = 5  # 每個查詢計時的次數

# 同一個問題，在兩種 schema 下的寫法
QUERIES = {
    "各類別銷售額": {
        "star": """
            SELECT p.Category, SUM(f.Amount) AS total_amount
            FROM FactSales f
            JOIN DimProduct p ON f.ProductKey = p.ProductKey
            GROUP BY p.Category
            ORDER BY p.Category""",
        "snowflake": """
            SELECT c.Category, SUM(f.Amount) AS total_amount
            FROM FactSales f
            JOIN DimProduct p ON f.ProductKey = p.ProductKey
            JOIN DimCategory c ON p.CategoryKey = c.CategoryKey
            GROUP BY c.Category
            ORDER BY c.Category""",
    },
    "各類別與品牌銷售額": {
        "star": """
            SELECT p.Category, p.Brand, SUM(f.Amount) AS total_amount
            FROM FactSales f
            JOIN DimProduct p ON f.ProductKey = p.ProductKey
            GROUP BY p.Category, p.Brand
            ORDER BY p.Category, p.Brand""",
        "snowflake": """
            SELECT c.Category, b.Brand, SUM(f.Amount) AS total_amount
            FROM FactSales f
            JOIN DimProduct p ON f.ProductKey = p.ProductKey
            JOIN DimCategory c ON p.CategoryKey = c.CategoryKey
            JOIN DimBrand b ON p.BrandKey = b.BrandKey
            GROUP BY c.Category, b.Brand
            ORDER BY c.Category, b.Brand""",
    },
}


def build_snowflake():
    """由 star 倉儲的資料建出 snowflake 倉儲。"""
    for path in (SNOW_PATH, Path(str(SNOW_PATH) + ".wal")):
        if path.exists():
            path.unlink()
    con = duckdb.connect(str(SNOW_PATH))
    con.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
    con.execute(f"ATTACH '{STAR_PATH}' AS star (READ_ONLY)")

    # 沒有變動的表：直接複製
    for name in ["DimDate", "DimCustomer", "DimStore"]:
        con.execute(f"INSERT INTO {name} SELECT * FROM star.{name}")

    # 新拆出來的表：取不重複的值，並給代理鍵
    con.execute("""
        INSERT INTO DimCategory
        SELECT CAST(row_number() OVER (ORDER BY Category) AS INTEGER), Category
        FROM (SELECT DISTINCT Category FROM star.DimProduct)""")
    con.execute("""
        INSERT INTO DimBrand
        SELECT CAST(row_number() OVER (ORDER BY Brand) AS INTEGER), Brand
        FROM (SELECT DISTINCT Brand FROM star.DimProduct)""")

    # DimProduct：Category、Brand 文字換成對應的 Key
    con.execute("""
        INSERT INTO DimProduct
        SELECT p.ProductKey, p.ProductID, p.ProductName, p.UnitPrice,
               c.CategoryKey, b.BrandKey
        FROM star.DimProduct p
        JOIN DimCategory c ON p.Category = c.Category
        JOIN DimBrand b ON p.Brand = b.Brand""")

    con.execute("INSERT INTO FactSales SELECT * FROM star.FactSales")
    con.execute("DETACH star")
    con.close()


def avg_ms(con, query):
    """先暖機一次，再跑 RUNS 次取平均（毫秒）。"""
    con.execute(query).fetchall()
    start = time.perf_counter()
    for _ in range(RUNS):
        con.execute(query).fetchall()
    return (time.perf_counter() - start) / RUNS * 1000


def count_joins(query):
    return query.upper().count("JOIN")


def main():
    print("建立 snowflake 倉儲…")
    build_snowflake()

    star = duckdb.connect(str(STAR_PATH), read_only=True)
    snow = duckdb.connect(str(SNOW_PATH), read_only=True)

    print(f"\n{'查詢':<12}{'schema':<11}{'JOIN 數':>8}{'平均時間(ms)':>14}{'結果相同':>10}")
    print("-" * 56)
    for name, versions in QUERIES.items():
        same = star.execute(versions["star"]).fetchall() == snow.execute(versions["snowflake"]).fetchall()
        for schema, con in (("star", star), ("snowflake", snow)):
            q = versions[schema]
            ok = "是" if same else "否"
            print(f"{name:<12}{schema:<11}{count_joins(q):>8}{avg_ms(con, q):>14.2f}{ok:>10}")

    # 儲存：Category、Brand 這兩欄的文字值總共存了幾份
    star_text = star.execute("SELECT COUNT(Category) + COUNT(Brand) FROM DimProduct").fetchone()[0]
    snow_text = snow.execute(
        "SELECT (SELECT COUNT(*) FROM DimCategory) + (SELECT COUNT(*) FROM DimBrand)"
    ).fetchone()[0]
    print("\n維度表中 Category 與 Brand 文字值的儲存份數")
    print(f"  star：{star_text}　snowflake：{snow_text}")
    print("資料庫檔案大小")
    print(f"  star：{STAR_PATH.stat().st_size / 1024:,.0f} KB"
          f"　snowflake：{SNOW_PATH.stat().st_size / 1024:,.0f} KB")
    print("（DuckDB 以固定大小的區塊配置空間，資料量小時檔案大小差異不明顯）")

    star.close()
    snow.close()


if __name__ == "__main__":
    main()