import pyodbc
import random
from datetime import datetime, timedelta
import string

def generate_test_data(rows=1000):
    """Generate larger test data set for more realistic index recommendations"""
    
    # Connection string for LocalDB
    conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};Server=(localdb)\\MSSQLLocalDB;Database=MedicalStorePOS;Trusted_Connection=yes;'
    
    try:
        print(f"Connecting to LocalDB...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Clear existing tables if they exist
        print("Clearing existing data...")
        cursor.execute("DELETE FROM Sales.SalesOrderDetail")
        cursor.execute("DELETE FROM Sales.SalesOrderHeader")
        cursor.execute("DELETE FROM Sales.Customer")
        conn.commit()
        
        # Generate random customers
        print(f"Generating {rows} customers...")
        customer_ids = []
        
        # First names and last names for random generation
        first_names = ['John', 'Jane', 'Robert', 'Mary', 'William', 'Patricia', 'David', 'Jennifer', 
                      'Michael', 'Linda', 'James', 'Elizabeth', 'Richard', 'Susan', 'Thomas', 'Sarah',
                      'Charles', 'Karen', 'Daniel', 'Nancy', 'Matthew', 'Lisa', 'Anthony', 'Betty']
        
        last_names = ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson',
                     'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin',
                     'Thompson', 'Garcia', 'Martinez', 'Robinson', 'Clark', 'Rodriguez', 'Lewis', 'Lee']
        
        # Generate customers
        for i in range(1, rows + 1):
            customer_id = i
            customer_ids.append(customer_id)
            
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"
            phone = f"555-{random.randint(1000, 9999)}"
            address = f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple', 'Cedar'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}"
            city = random.choice(['Springfield', 'Rivertown', 'Lakeside', 'Hillcrest', 'Maplewood', 'Oakdale', 'Pine Valley', 'Cedar Hills'])
            state = random.choice(['CA', 'TX', 'NY', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI'])
            zip_code = f"{random.randint(10000, 99999)}"
            
            cursor.execute("""
                INSERT INTO Sales.Customer (CustomerID, FirstName, LastName, Email, Phone, Address, City, State, ZipCode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (customer_id, first_name, last_name, email, phone, address, city, state, zip_code))
            
            if i % 100 == 0:
                conn.commit()
                print(f"  Inserted {i} customers...")
        
        conn.commit()
        print(f"Customers generated.")
        
        # Generate orders (about 3 orders per customer on average)
        print(f"Generating orders...")
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2022, 12, 31)
        order_ids = []
        
        for order_id in range(1001, 1001 + rows * 3):
            customer_id = random.choice(customer_ids)
            days = (end_date - start_date).days
            order_date = start_date + timedelta(days=random.randint(0, days))
            ship_date = order_date + timedelta(days=random.randint(1, 10))
            total_due = round(random.uniform(10, 1000), 2)
            status = random.randint(1, 5)
            
            order_ids.append(order_id)
            
            cursor.execute("""
                INSERT INTO Sales.SalesOrderHeader (SalesOrderID, CustomerID, OrderDate, ShipDate, TotalDue, Status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, customer_id, order_date, ship_date, total_due, status))
            
            if order_id % 100 == 0:
                conn.commit()
                print(f"  Inserted {order_id - 1000} orders...")
        
        conn.commit()
        print(f"Orders generated.")
        
        # Generate order details (2-5 items per order)
        print(f"Generating order details...")
        detail_id = 10001
        
        # Product IDs and prices for random generation
        products = {}
        for i in range(700, 800):
            products[i] = round(random.uniform(5, 500), 2)
        
        for order_id in order_ids:
            # 2 to 5 items per order
            for _ in range(random.randint(2, 5)):
                product_id = random.choice(list(products.keys()))
                unit_price = products[product_id]
                order_qty = random.randint(1, 10)
                line_total = round(unit_price * order_qty, 2)
                
                cursor.execute("""
                    INSERT INTO Sales.SalesOrderDetail (SalesOrderDetailID, SalesOrderID, ProductID, OrderQty, UnitPrice, LineTotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (detail_id, order_id, product_id, order_qty, unit_price, line_total))
                
                detail_id += 1
            
            if order_id % 100 == 0:
                conn.commit()
                print(f"  Processed details for {order_id - 1000} orders...")
        
        conn.commit()
        print(f"Order details generated.")
        
        # Create some indexes to demonstrate in the tool
        print("Creating statistics...")
        cursor.execute("UPDATE STATISTICS Sales.Customer WITH FULLSCAN")
        cursor.execute("UPDATE STATISTICS Sales.SalesOrderHeader WITH FULLSCAN")
        cursor.execute("UPDATE STATISTICS Sales.SalesOrderDetail WITH FULLSCAN")
        
        # Count the rows
        cursor.execute("SELECT COUNT(*) FROM Sales.Customer")
        customer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Sales.SalesOrderHeader")
        order_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Sales.SalesOrderDetail")
        detail_count = cursor.fetchone()[0]
        
        print(f"\nData generation complete!")
        print(f"  - {customer_count} customers")
        print(f"  - {order_count} orders")
        print(f"  - {detail_count} order details")
        print("\nYour database is ready for index analysis.")
        
        conn.close()
        return True
        
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    import sys
    rows = 1000
    if len(sys.argv) > 1:
        try:
            rows = int(sys.argv[1])
        except ValueError:
            print("Invalid number of rows. Using default of 1000.")
    
    generate_test_data(rows)