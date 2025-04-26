import pyodbc
import sys

def create_database(db_name='MedicalStorePOS'):
    """Create the database and required schema if it doesn't exist"""
    
    # Connection strings for connecting to master (to create database)
    conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;Database=master;Trusted_Connection=yes;'
    
    try:
        # Connect to master database with autocommit
        print(f"Connecting to LocalDB master database...")
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT database_id FROM sys.databases WHERE name = '{db_name}'")
        result = cursor.fetchone()
        
        if not result:
            print(f"Database '{db_name}' does not exist. Creating it now...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
        
        conn.close()
        
        # Now connect to the database to create schema
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};Server=(localdb)\\MSSQLLocalDB;Database={db_name};Trusted_Connection=yes;'
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Check if Sales schema exists
        cursor.execute("SELECT schema_id FROM sys.schemas WHERE name = 'Sales'")
        result = cursor.fetchone()
        
        if not result:
            print("Creating Sales schema...")
            cursor.execute("CREATE SCHEMA Sales")
            print("Sales schema created successfully.")
        else:
            print("Sales schema already exists.")
        
        # Create sample tables for testing if they don't exist
        print("Creating sample tables if they don't exist...")
        
        # Customer table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Customer' AND schema_id = SCHEMA_ID('Sales'))
        BEGIN
            CREATE TABLE Sales.Customer (
                CustomerID INT PRIMARY KEY,
                FirstName NVARCHAR(50),
                LastName NVARCHAR(50),
                Email NVARCHAR(100),
                Phone NVARCHAR(20),
                Address NVARCHAR(100),
                City NVARCHAR(50),
                State NVARCHAR(2),
                ZipCode NVARCHAR(10)
            )
            
            -- Insert sample data
            INSERT INTO Sales.Customer (CustomerID, FirstName, LastName, Email, Phone, Address, City, State, ZipCode)
            VALUES
                (1, 'John', 'Smith', 'john.smith@example.com', '555-1234', '123 Main St', 'Anytown', 'CA', '90210'),
                (2, 'Jane', 'Doe', 'jane.doe@example.com', '555-4321', '456 Oak St', 'Somewhere', 'NY', '10001'),
                (3, 'Sarah', 'Johnson', 'sarah.j@example.com', '555-5678', '789 Pine Ave', 'Nowhere', 'TX', '75001'),
                (4, 'Robert', 'Smith', 'rob.smith@example.com', '555-8765', '321 Elm St', 'Anywhere', 'FL', '33101')
            
            PRINT 'Customer table created with sample data.'
        END
        ELSE
            PRINT 'Customer table already exists.'
        """)
        
        # SalesOrderHeader table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SalesOrderHeader' AND schema_id = SCHEMA_ID('Sales'))
        BEGIN
            CREATE TABLE Sales.SalesOrderHeader (
                SalesOrderID INT PRIMARY KEY,
                CustomerID INT FOREIGN KEY REFERENCES Sales.Customer(CustomerID),
                OrderDate DATETIME,
                ShipDate DATETIME,
                TotalDue MONEY,
                Status TINYINT
            )
            
            -- Insert sample data
            INSERT INTO Sales.SalesOrderHeader (SalesOrderID, CustomerID, OrderDate, ShipDate, TotalDue, Status)
            VALUES
                (1001, 1, '2020-01-15', '2020-01-20', 150.25, 5),
                (1002, 2, '2020-02-10', '2020-02-15', 245.99, 5),
                (1003, 3, '2020-03-05', '2020-03-10', 50.75, 5),
                (1004, 1, '2020-04-20', '2020-04-25', 125.50, 5),
                (1005, 3, '2020-05-12', '2020-05-17', 89.99, 5),
                (1006, 2, '2020-06-30', '2020-07-05', 175.25, 5),
                (1007, 4, '2020-07-22', '2020-07-27', 320.00, 5),
                (1008, 1, '2020-08-15', '2020-08-20', 45.75, 5)
            
            PRINT 'SalesOrderHeader table created with sample data.'
        END
        ELSE
            PRINT 'SalesOrderHeader table already exists.'
        """)
        
        # SalesOrderDetail table
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SalesOrderDetail' AND schema_id = SCHEMA_ID('Sales'))
        BEGIN
            CREATE TABLE Sales.SalesOrderDetail (
                SalesOrderDetailID INT PRIMARY KEY,
                SalesOrderID INT FOREIGN KEY REFERENCES Sales.SalesOrderHeader(SalesOrderID),
                ProductID INT,
                OrderQty SMALLINT,
                UnitPrice MONEY,
                LineTotal MONEY
            )
            
            -- Insert sample data
            INSERT INTO Sales.SalesOrderDetail (SalesOrderDetailID, SalesOrderID, ProductID, OrderQty, UnitPrice, LineTotal)
            VALUES
                (10001, 1001, 776, 2, 25.50, 51.00),
                (10002, 1001, 777, 1, 99.25, 99.25),
                (10003, 1002, 778, 3, 45.00, 135.00),
                (10004, 1002, 776, 2, 25.50, 51.00),
                (10005, 1002, 779, 1, 59.99, 59.99),
                (10006, 1003, 780, 2, 25.37, 50.74),
                (10007, 1004, 776, 5, 25.10, 125.50),
                (10008, 1005, 778, 1, 45.00, 45.00),
                (10009, 1005, 781, 1, 44.99, 44.99),
                (10010, 1006, 776, 3, 25.00, 75.00),
                (10011, 1006, 782, 2, 50.12, 100.24),
                (10012, 1007, 783, 1, 320.00, 320.00),
                (10013, 1008, 776, 1, 25.75, 25.75),
                (10014, 1008, 784, 1, 20.00, 20.00)
            
            PRINT 'SalesOrderDetail table created with sample data.'
        END
        ELSE
            PRINT 'SalesOrderDetail table already exists.'
        """)
        
        conn.commit()
        print(f"Database setup complete. Your '{db_name}' database is now ready to use with the AutoIndex tool.")
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"Database setup error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    try:
        db_name = sys.argv[1] if len(sys.argv) > 1 else 'MedicalStorePOS'
        create_database(db_name)
    except Exception as e:
        print(f"Error: {e}")
        print("Usage: python setup_database.py [database_name]")
        print("If database_name is not provided, 'MedicalStorePOS' will be used.")