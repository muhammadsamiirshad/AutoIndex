import pyodbc
import re
import os
import sys
import sqlparse
from utils import create_sql_connection_string

# Make connection string a module-level variable so it can be overridden by GUI
# Using r-string (raw string) to handle backslashes properly
conn_str = create_sql_connection_string(
    server=r'(localdb)\MSSQLLocalDB', 
    database='MedicalStorePOS',
    auth_type='windows'
)
current_database_name = 'MedicalStorePOS'  # Default database name, will be extracted from conn_str when changed

def get_direct_recommendations(workload_file):
    """Get index recommendations directly using SQL Server's DMVs"""
    
    # Use the module-level connection string (can be overridden by the GUI)
    global conn_str, current_database_name
    
    try:
        # Extract the current database name from the connection string
        db_match = re.search(r'Database=([^;]+)', conn_str, re.IGNORECASE)
        if db_match:
            current_database_name = db_match.group(1)
        
        server_match = re.search(r'Server=([^;]+)', conn_str, re.IGNORECASE)
        server_name = server_match.group(1) if server_match else "unknown"
        
        print(f"Connecting to {server_name}, database: {current_database_name}...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Clear existing missing index data
        print("Clearing existing missing index data...")
        cursor.execute(f"""
            -- Clear the procedure cache to get a fresh start
            DBCC FREEPROCCACHE;
            
            -- Clear query store data
            ALTER DATABASE [{current_database_name}] SET QUERY_STORE CLEAR;
        """)
        
        # Load and execute each query in the workload
        print("Loading workload queries...")
        with open(workload_file, 'r', errors='ignore') as file:
            raw_text = file.read()
            
            # Remove SQL comments
            raw_text = re.sub(r'--.*?\n', '\n', raw_text)  # Remove single line comments
            raw_text = re.sub(r'/\*[\s\S]*?\*/', '', raw_text)  # Remove multi-line comments
            
            # Split by semicolons to get individual queries
            raw_queries = re.split(r';\s*', raw_text)
            
            queries = []
            for sql in raw_queries:
                sql = sql.strip()
                if not sql:
                    continue
                    
                # Only consider SELECT statements (for index recommendations)
                if re.search(r'^\s*SELECT\s+', sql, re.IGNORECASE):
                    queries.append(sql)
        
        print(f"Executing {len(queries)} queries to generate index statistics...")
        for i, sql in enumerate(queries):
            try:
                print(f"Executing query {i+1}/{len(queries)}: {sql[:50]}...")
                cursor.execute(sql)
                
                # Consume the results to ensure query completes fully
                while cursor.nextset():
                    pass
            except Exception as e:
                print(f"Error executing query: {e}")
                continue
        
        # Get recommendations from missing index DMVs
        print("\nGetting index recommendations from SQL Server DMVs...")
        cursor.execute("""
            SELECT 
                OBJECT_SCHEMA_NAME(mid.object_id) AS SchemaName,
                OBJECT_NAME(mid.object_id) AS TableName,
                migs.avg_total_user_cost * (migs.avg_user_impact / 100.0) * (migs.user_seeks + migs.user_scans) AS Improvement,
                migs.user_seeks + migs.user_scans AS user_events,
                'CREATE INDEX IX_' + OBJECT_NAME(mid.object_id) + '_' 
                    + REPLACE(REPLACE(REPLACE(ISNULL(mid.equality_columns, '') 
                    + CASE WHEN mid.equality_columns IS NOT NULL AND mid.inequality_columns IS NOT NULL THEN '_' ELSE '' END
                    + ISNULL(mid.inequality_columns, ''), ', ', '_'), '[', ''), ']', '') 
                    + ' ON ' + mid.statement 
                    + ' (' + ISNULL(mid.equality_columns, '')
                    + CASE WHEN mid.equality_columns IS NOT NULL AND mid.inequality_columns IS NOT NULL THEN ', ' ELSE '' END 
                    + ISNULL(mid.inequality_columns, '') + ')'
                    + ISNULL(' INCLUDE (' + mid.included_columns + ')', '') AS CreateStatement
            FROM sys.dm_db_missing_index_groups mig
            INNER JOIN sys.dm_db_missing_index_group_stats migs
                ON migs.group_handle = mig.index_group_handle
            INNER JOIN sys.dm_db_missing_index_details mid
                ON mig.index_handle = mid.index_handle
            WHERE mid.database_id = DB_ID()
            ORDER BY Improvement DESC;
        """)
        
        results = cursor.fetchall()
        
        print("\n" + "#" * 20 + " RECOMMENDED INDEXES " + "#" * 20)
        
        if not results or len(results) == 0:
            print("No index recommendations found.")
            
            print("\nLet's check for existing indexes for common schemas:")
            try:
                # Get all schema names first
                cursor.execute("SELECT DISTINCT s.name FROM sys.schemas s JOIN sys.tables t ON s.schema_id = t.schema_id WHERE t.is_ms_shipped = 0")
                schemas = [row[0] for row in cursor.fetchall()]
                
                if not schemas:
                    schemas = ['dbo']  # Default to dbo if no schemas found
                    
                print(f"Found schemas: {', '.join(schemas)}")
                
                for schema_name in schemas:
                    cursor.execute(f"""
                        SELECT 
                            s.name AS schema_name,
                            t.name AS table_name,
                            i.name AS index_name,
                            i.type_desc,
                            STUFF((SELECT ', ' + c.name FROM sys.index_columns ic
                                INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                                WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id 
                                AND ic.is_included_column = 0
                                ORDER BY ic.key_ordinal
                                FOR XML PATH('')), 1, 2, '') AS key_columns,
                            STUFF((SELECT ', ' + c.name FROM sys.index_columns ic
                                INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                                WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id 
                                AND ic.is_included_column = 1
                                ORDER BY ic.key_ordinal
                                FOR XML PATH('')), 1, 2, '') AS included_columns
                        FROM sys.indexes i
                        INNER JOIN sys.tables t ON i.object_id = t.object_id
                        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                        WHERE i.index_id > 0   -- Skip heaps
                        AND i.is_primary_key = 0   -- Skip primary keys
                        AND i.is_unique_constraint = 0  -- Skip unique constraints
                        AND t.is_ms_shipped = 0   -- Skip system tables
                        AND s.name = '{schema_name}'
                        ORDER BY schema_name, table_name, index_name;
                    """)
                    
                    existing_indexes = cursor.fetchall()
                    
                    if existing_indexes and len(existing_indexes) > 0:
                        print(f"\nExisting indexes found in schema {schema_name}:")
                        for idx in existing_indexes:
                            print(f"  {idx.schema_name}.{idx.table_name}: {idx.index_name} ({idx.type_desc})")
                            print(f"    Columns: {idx.key_columns}")
                            if idx.included_columns:
                                print(f"    Included: {idx.included_columns}")
                    else:
                        print(f"\nNo existing indexes found in schema {schema_name}.")
            except Exception as e:
                print(f"Error checking existing indexes: {e}")
                
            print("\nConsider manually creating a primary key or clustered index on each table.")
        else:
            for i, row in enumerate(results):
                print(f"\nINDEX {i+1}:")
                print(f"  Table: {row.SchemaName}.{row.TableName}")
                print(f"  Estimated Improvement: {row.Improvement:.2f}")
                print(f"  User Events (seeks + scans): {row.user_events}")
                print(f"  CREATE Statement: {row.CreateStatement}")
                
                if i < len(results) - 1:
                    print("-" * 60)
                    
        return True
        
    except pyodbc.Error as e:
        print(f"Database connection error: {e}")
        # Print more details about the connection attempt 
        print(f"Tried to connect with: {conn_str.replace(conn_str.split('PWD=')[1] if 'PWD=' in conn_str else '', '****')}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    workload_file = "workload.sql"
    if len(sys.argv) > 1:
        workload_file = sys.argv[1]
    
    get_direct_recommendations(workload_file)