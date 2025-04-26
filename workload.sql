-- Basic SQL queries for index recommendation analysis
-- Query 1: Filter on CustomerID
SELECT * FROM Sales.Customer WHERE CustomerID BETWEEN 100 AND 200;

-- Query 2: Filter on LastName with LIKE (good candidate for index)
SELECT * FROM Sales.Customer WHERE LastName LIKE 'S%';

-- Query 3: Date range query (good candidate for index)
SELECT * FROM Sales.SalesOrderHeader WHERE OrderDate BETWEEN '2020-01-01' AND '2020-06-30';

-- Query 4: Multiple filters on order details
SELECT * FROM Sales.SalesOrderDetail WHERE ProductID = 776 AND OrderQty > 1;

-- Query 5: JOIN with WHERE clause (good candidate for indexes)
SELECT c.CustomerID, c.LastName, c.FirstName, oh.OrderDate, oh.TotalDue 
FROM Sales.Customer c 
JOIN Sales.SalesOrderHeader oh ON c.CustomerID = oh.CustomerID 
WHERE oh.OrderDate > '2021-01-01' AND c.State = 'CA';

-- Query 6: Complex query with multiple joins
SELECT c.CustomerID, c.LastName, c.FirstName, 
       oh.OrderDate, oh.TotalDue,
       od.ProductID, od.OrderQty, od.UnitPrice
FROM Sales.Customer c 
JOIN Sales.SalesOrderHeader oh ON c.CustomerID = oh.CustomerID
JOIN Sales.SalesOrderDetail od ON oh.SalesOrderID = od.SalesOrderID
WHERE oh.OrderDate BETWEEN '2021-01-01' AND '2021-12-31'
  AND od.UnitPrice > 100
ORDER BY oh.OrderDate DESC;

-- Query 7: Query with GROUP BY (aggregate query)
SELECT c.State, COUNT(DISTINCT c.CustomerID) AS CustomerCount, 
       SUM(oh.TotalDue) AS TotalSales
FROM Sales.Customer c
JOIN Sales.SalesOrderHeader oh ON c.CustomerID = oh.CustomerID
GROUP BY c.State
ORDER BY TotalSales DESC;

-- Query 8: Subquery example
SELECT * FROM Sales.Customer c
WHERE EXISTS (
    SELECT 1 FROM Sales.SalesOrderHeader oh
    WHERE oh.CustomerID = c.CustomerID
    AND oh.TotalDue > 500
);

-- Query 9: Query with multiple conditions for testing compound indexes
SELECT oh.SalesOrderID, oh.OrderDate, oh.TotalDue
FROM Sales.SalesOrderHeader oh
WHERE oh.CustomerID BETWEEN 100 AND 200
  AND oh.OrderDate > '2021-06-01'
  AND oh.TotalDue > 200
ORDER BY oh.OrderDate;

-- Query 10: Query with ORDER BY and TOP which can benefit from covering index
SELECT TOP 100 c.CustomerID, c.FirstName, c.LastName, c.Email
FROM Sales.Customer c
WHERE c.State IN ('CA', 'TX', 'NY', 'FL')
ORDER BY c.LastName, c.FirstName;