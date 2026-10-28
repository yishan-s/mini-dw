"""產生模擬 OLTP 資料（3NF），輸出 5 個 CSV 到專案的 data/ 資料夾。

執行方式（在專案根目錄）：
    python src/generate_data.py

固定亂數種子，每次執行結果相同。資料全為虛構，不含任何真實個資。
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
N_CUSTOMERS = 500
N_PRODUCTS = 100
N_ORDERS = 20_000
START_DATE = date(2024, 1, 1)
END_DATE = date(2025, 12, 31)  # 連續 2 年

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SURNAMES = list("陳林黃張李王吳劉蔡楊許鄭謝郭洪曾邱廖賴徐")
GIVEN = list("怡君雅婷宗翰承恩家豪佳穎冠宇欣妤志明俊宏淑芬美玲建宏柏翰詩涵")

# (城市, 區域)
CITY_REGION = [
    ("台北", "北部"), ("新北", "北部"), ("桃園", "北部"), ("新竹", "北部"),
    ("台中", "中部"), ("彰化", "中部"),
    ("台南", "南部"), ("高雄", "南部"), ("屏東", "南部"),
    ("花蓮", "東部"),
]

# 類別 -> 單價範圍
CATEGORIES = {
    "飲料": (20, 80),
    "零食": (25, 120),
    "日用品": (40, 300),
    "生鮮": (30, 250),
    "3C配件": (150, 1500),
}
BRANDS = [f"品牌{c}" for c in "ABCDEFGHIJ"]


def make_customers(rng):
    rows = []
    for i in range(1, N_CUSTOMERS + 1):
        name = rng.choice(SURNAMES) + "".join(rng.choices(GIVEN, k=2))
        city = rng.choice(CITY_REGION)[0]
        if rng.random() < 0.02:  # 約 2% 故意留空，之後練習在 ETL 清洗
            city = ""
        rows.append((f"C{i:04d}", name, city))
    return pd.DataFrame(rows, columns=["CustomerID", "Name", "City"])


def make_products(rng):
    rows = []
    cats = list(CATEGORIES)
    for i in range(1, N_PRODUCTS + 1):
        cat = cats[(i - 1) % len(cats)]
        lo, hi = CATEGORIES[cat]
        price = rng.randrange(lo, hi + 1, 5)
        rows.append((f"P{i:03d}", f"{cat}商品{i:03d}", cat, rng.choice(BRANDS), price))
    return pd.DataFrame(
        rows, columns=["ProductID", "ProductName", "Category", "Brand", "UnitPrice"]
    )


def make_stores():
    rows = []
    for i, (city, region) in enumerate(CITY_REGION, start=1):
        rows.append((f"S{i:02d}", f"{city}店", city, region))
    return pd.DataFrame(rows, columns=["StoreID", "StoreName", "City", "Region"])


def make_orders_and_details(rng, customers, products, stores):
    days = (END_DATE - START_DATE).days
    cust_ids = customers["CustomerID"].tolist()
    store_ids = stores["StoreID"].tolist()
    prod_ids = products["ProductID"].tolist()

    orders, details = [], []
    for i in range(1, N_ORDERS + 1):
        order_id = f"O{i:06d}"
        order_date = START_DATE + timedelta(days=rng.randint(0, days))
        orders.append(
            (order_id, order_date.isoformat(), rng.choice(cust_ids), rng.choice(store_ids))
        )
        for pid in rng.sample(prod_ids, k=rng.randint(1, 5)):  # 同一張訂單商品不重複
            details.append((order_id, pid, rng.randint(1, 5)))

    orders_df = pd.DataFrame(
        orders, columns=["OrderID", "OrderDate", "CustomerID", "StoreID"]
    ).sort_values(["OrderDate", "OrderID"])
    details_df = pd.DataFrame(details, columns=["OrderID", "ProductID", "Quantity"])
    return orders_df, details_df


def main():
    rng = random.Random(SEED)
    DATA_DIR.mkdir(exist_ok=True)

    customers = make_customers(rng)
    products = make_products(rng)
    stores = make_stores()
    orders, details = make_orders_and_details(rng, customers, products, stores)

    tables = {
        "customers": customers,
        "products": products,
        "stores": stores,
        "orders": orders,
        "order_details": details,
    }
    for name, df in tables.items():
        df.to_csv(DATA_DIR / f"{name}.csv", index=False, encoding="utf-8")
        print(f"{name}.csv：{len(df):,} 筆")
    print(f"已輸出到 {DATA_DIR}")


if __name__ == "__main__":
    main()