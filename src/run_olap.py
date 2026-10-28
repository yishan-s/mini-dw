"""執行 sql/olap_queries.sql 裡的所有查詢，並印出每個查詢的結果。

執行方式（在專案根目錄，需先跑過 etl.py）：
    python src/run_olap.py
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "warehouse.duckdb"
SQL_FILE = ROOT / "sql" / "olap_queries.sql"


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    text = SQL_FILE.read_text(encoding="utf-8")
    for chunk in text.split(";"):  # 每個查詢以分號結尾
        query = chunk.strip()
        if not query:
            continue
        title = next((ln[2:].strip() for ln in query.splitlines() if ln.startswith("--")), "")
        print("=" * 60)
        print(title)
        print("=" * 60)
        print(con.sql(query))
    con.close()


if __name__ == "__main__":
    main()