-- Snowflake schema：DimProduct 正規化，拆成 DimProduct、DimCategory、DimBrand
-- 其餘維度表與事實表和 star schema 相同
DROP TABLE IF EXISTS FactSales;
DROP TABLE IF EXISTS DimProduct;
DROP TABLE IF EXISTS DimCategory;
DROP TABLE IF EXISTS DimBrand;
DROP TABLE IF EXISTS DimDate;
DROP TABLE IF EXISTS DimCustomer;
DROP TABLE IF EXISTS DimStore;

CREATE TABLE DimDate (
    DateKey    INTEGER PRIMARY KEY,
    FullDate   DATE    NOT NULL,
    Year       INTEGER NOT NULL,
    Quarter    INTEGER NOT NULL,
    Month      INTEGER NOT NULL,
    Week       INTEGER NOT NULL,
    DayOfWeek  INTEGER NOT NULL
);

CREATE TABLE DimCategory (
    CategoryKey  INTEGER PRIMARY KEY,
    Category     VARCHAR NOT NULL
);

CREATE TABLE DimBrand (
    BrandKey  INTEGER PRIMARY KEY,
    Brand     VARCHAR NOT NULL
);

CREATE TABLE DimProduct (
    ProductKey   INTEGER PRIMARY KEY,
    ProductID    VARCHAR NOT NULL,
    ProductName  VARCHAR NOT NULL,
    UnitPrice    INTEGER NOT NULL,
    CategoryKey  INTEGER NOT NULL REFERENCES DimCategory(CategoryKey),
    BrandKey     INTEGER NOT NULL REFERENCES DimBrand(BrandKey)
);

CREATE TABLE DimCustomer (
    CustomerKey  INTEGER PRIMARY KEY,
    CustomerID   VARCHAR NOT NULL,
    Name         VARCHAR NOT NULL,
    City         VARCHAR NOT NULL
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
    Amount       INTEGER NOT NULL
);