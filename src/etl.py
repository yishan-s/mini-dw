"""ETL：把模擬 OLTP 的 CSV 轉成 star schema，載入 DuckDB 資料倉儲。

執行方式（在專案根目錄）：
    python src/etl.py

每次執行都會重建倉儲裡的資料表，可以放心重跑。
"""

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SQL_FILE = ROOT / "sql" / "schema_star.sql"
DB_PATH = ROOT / "warehouse.duckdb"

# 載入順序：先維度表，最後才是事實表（事實表有外部鍵指向維度表）
LOAD_ORDER = ["DimDate", "DimProduct", "DimCustomer", "DimStore", "FactSales"]


# ---------------------------------------------------------------- Extract
def extract():
    """Extract：讀入 5 個來源 CSV。"""
    print("[Extract] 讀取來源 CSV")
    src = {
        "customers": pd.read_csv(DATA_DIR / "customers.csv"),
        "products": pd.read_csv(DATA_DIR / "products.csv"),
        "stores": pd.read_csv(DATA_DIR / "stores.csv"),
        "orders": pd.read_csv(DATA_DIR / "orders.csv"),
        "order_details": pd.read_csv(DATA_DIR / "order_details.csv"),
    }
    for name, df in src.items():
        print(f"  {name}：{len(df):,} 筆")
    return src


# -------------------------------------------------------------- Transform
def add_surrogate_key(df, key_name):
    """加上代理鍵（1, 2, 3, ...）當作第一欄。"""
    df = df.reset_index(drop=True)
    df.insert(0, key_name, list(range(1, len(df) + 1)))
    return df


def transform(src):
    """Transform：清洗、建立維度表與事實表。"""
    print("[Transform] 清洗並建立維度表與事實表")

    # 1. 清洗：去除重複列、補齊缺值、統一型別
    customers = src["customers"].drop_duplicates("CustomerID").copy()
    customers["City"] = customers["City"].fillna("").str.strip().replace("", "未知")
    products = src["products"].drop_duplicates("ProductID").copy()
    stores = src["stores"].drop_duplicates("StoreID").copy()
    orders = src["orders"].drop_duplicates("OrderID").copy()
    orders["OrderDate"] = pd.to_datetime(orders["OrderDate"])
    details = src["order_details"].drop_duplicates(["OrderID", "ProductID"]).copy()

    # 2. 維度表：加上代理鍵
    dim_product = add_surrogate_key(
        products[["ProductID", "ProductName", "Category", "Brand", "UnitPrice"]],
        "ProductKey",
    )
    dim_customer = add_surrogate_key(
        customers[["CustomerID", "Name", "City"]], "CustomerKey"
    )
    dim_store = add_surrogate_key(
        stores[["StoreID", "StoreName", "City", "Region"]], "StoreKey"
    )

    # 3. DimDate：從訂單日期的最小值到最大值，每天一列
    days = pd.date_range(orders["OrderDate"].min(), orders["OrderDate"].max(), freq="D")
    dim_date = pd.DataFrame({"FullDate": days})
    d = dim_date["FullDate"].dt
    dim_date.insert(0, "DateKey", d.strftime("%Y%m%d").astype(int))
    dim_date["Year"] = d.year
    dim_date["Quarter"] = d.quarter
    dim_date["Month"] = d.month
    dim_date["Week"] = d.isocalendar().week.astype(int)
    dim_date["DayOfWeek"] = d.dayofweek + 1  # 1 = 星期一 … 7 = 星期日
    dim_date["FullDate"] = d.date

    # 4. 事實表：明細 → 補上訂單資訊 → 換成各維度的代理鍵 → 計算金額
    fact = (
        details.merge(
            orders[["OrderID", "OrderDate", "CustomerID", "StoreID"]],
            on="OrderID", how="left",
        )
        .merge(dim_product[["ProductKey", "ProductID", "UnitPrice"]], on="ProductID", how="left")
        .merge(dim_customer[["CustomerKey", "CustomerID"]], on="CustomerID", how="left")
        .merge(dim_store[["StoreKey", "StoreID"]], on="StoreID", how="left")
    )
    fact["DateKey"] = fact["OrderDate"].dt.strftime("%Y%m%d").astype(int)
    fact["Amount"] = fact["Quantity"] * fact["UnitPrice"]

    fact_cols = ["DateKey", "ProductKey", "CustomerKey", "StoreKey", "Quantity", "Amount"]
    if fact[fact_cols].isna().any().any():
        raise ValueError("事實表有對不到維度的資料，請檢查來源資料")
    fact = fact[fact_cols]

    tables = {
        "DimDate": dim_date,
        "DimProduct": dim_product,
        "DimCustomer": dim_customer,
        "DimStore": dim_store,
        "FactSales": fact,
    }

    # 驗證用的預期值：直接由來源明細與商品單價算出
    unit_price = products.set_index("ProductID")["UnitPrice"]
    expected = {
        "rows": len(details),
        "amount": int((details["Quantity"] * details["ProductID"].map(unit_price)).sum()),
    }
    return tables, expected


# ------------------------------------------------------------------- Load
def load(tables):
    """Load：建立資料表，依序載入維度表與事實表。"""
    print("[Load] 寫入 DuckDB 資料倉儲")
    con = duckdb.connect(str(DB_PATH))
    con.execute(SQL_FILE.read_text(encoding="utf-8"))  # 內含 DROP + CREATE，所以可重跑
    for name in LOAD_ORDER:
        df = tables[name]
        cols = ", ".join(df.columns)
        con.register("_tmp", df)
        con.execute(f"INSERT INTO {name} ({cols}) SELECT {cols} FROM _tmp")
        con.unregister("_tmp")
        print(f"  {name}：{len(df):,} 筆")
    return con


# ----------------------------------------------------------------- Verify
def verify(con, expected):
    """驗證：核對事實表筆數與總銷售金額是否跟來源一致。"""
    rows, total = con.execute("SELECT COUNT(*), SUM(Amount) FROM FactSales").fetchone()
    print("[Verify] 核對來源與倉儲")
    print(f"  筆數：來源 {expected['rows']:,}，倉儲 {rows:,}")
    print(f"  總金額：來源 {expected['amount']:,}，倉儲 {int(total):,}")
    if rows != expected["rows"] or int(total) != expected["amount"]:
        raise SystemExit("驗證失敗：來源與倉儲不一致，已中止。")
    print("  驗證通過")


def main():
    src = extract()
    tables, expected = transform(src)
    con = load(tables)
    verify(con, expected)
    con.close()
    print(f"完成：{DB_PATH}")


if __name__ == "__main__":
    main()