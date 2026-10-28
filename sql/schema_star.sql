-- Star schema：1 張事實表 + 4 張維度表
-- 先刪事實表，再刪維度表（外部鍵依賴順序）
DROP TABLE IF EXISTS FactSales;
DROP TABLE IF EXISTS DimDate;
DROP TABLE IF EXISTS DimProduct;
DROP TABLE IF EXISTS DimCustomer;
DROP TABLE IF EXISTS DimStore;

CREATE TABLE DimDate (
    DateKey    INTEGER PRIMARY KEY,   -- 格式 YYYYMMDD，例如 20240101
    FullDate   DATE    NOT NULL,
    Year       INTEGER NOT NULL,
    Quarter    INTEGER NOT NULL,
    Month      INTEGER NOT NULL,
    Week       INTEGER NOT NULL,
    DayOfWeek  INTEGER NOT NULL       -- 1 = 星期一 … 7 = 星期日
);

CREATE TABLE DimProduct (
    ProductKey   INTEGER PRIMARY KEY, -- 代理鍵（surrogate key）
    ProductID    VARCHAR NOT NULL,    -- 來源系統的商品編號
    ProductName  VARCHAR NOT NULL,
    Category     VARCHAR NOT NULL,
    Brand        VARCHAR NOT NULL,
    UnitPrice    INTEGER NOT NULL
);

CREATE TABLE DimCustomer (
    CustomerKey  INTEGER PRIMARY KEY,
    CustomerID   VARCHAR NOT NULL,
    Name         VARCHAR NOT NULL,
    City         VARCHAR NOT NULL     -- 來源的空白值在 ETL 轉成「未知」
);

CREATE TABLE DimStore (
    StoreKey   INTEGER PRIMARY KEY,
    StoreID    VARCHAR NOT NULL,
    StoreName  VARCHAR NOT NULL,
    City       VARCHAR NOT NULL,
    Region     VARCHAR NOT NULL
);

CREATE TABLE FactSales (
    DateKey      INTEGER NOT NULL REFERENCES DimDate(DateKey),
    ProductKey   INTEGER NOT NULL REFERENCES DimProduct(ProductKey),
    CustomerKey  INTEGER NOT NULL REFERENCES DimCustomer(CustomerKey),
    StoreKey     INTEGER NOT NULL REFERENCES DimStore(StoreKey),
    Quantity     INTEGER NOT NULL,
    Amount       INTEGER NOT NULL     -- = Quantity × UnitPrice
);