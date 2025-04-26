# Copyright (c) 2022 Huawei Technologies Co.,Ltd.
#
# openGauss is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
import sys
from typing import List
import logging
from contextlib import contextmanager

import psycopg2

sys.path.append('..')

from .common import BaseExecutor

try:
    import pyodbc
    PYODBC_IMPORTED = True
except ImportError:
    PYODBC_IMPORTED = False
    logging.warning("Failed to import pyodbc. SQL Server support will not be available.")


class DriverExecutor(BaseExecutor):
    def __init__(self, *arg):
        super(DriverExecutor, self).__init__(*arg)
        self.conn = None
        self.cur = None
        with self.session():
            pass

    def __init_conn_handle(self):
        self.conn = psycopg2.connect(dbname=self.dbname,
                                     user=self.user,
                                     password=self.password,
                                     host=self.host,
                                     port=self.port,
                                     application_name='DBMind-index-advisor')
        self.cur = self.conn.cursor()

    def __execute(self, sql):
        if self.cur.closed:
            self.__init_conn_handle()
        try:
            self.cur.execute(sql)
            self.conn.commit()
            if self.cur.rowcount == -1:
                return
            return [(self.cur.statusmessage,)] + self.cur.fetchall()
        except psycopg2.ProgrammingError:
            return [('ERROR',)]
        except Exception as e:
            logging.warning('Found %s while executing SQL statement.', e)
            return [('ERROR ' + str(e),)]
        finally:
            self.conn.rollback()

    def execute_sqls(self, sqls) -> List[str]:
        results = []
        sqls = ['set current_schema = %s' % self.get_schema()] + sqls
        for sql in sqls:
            res = self.__execute(sql)
            if res:
                results.extend(res)
        return results

    def __close_conn(self):
        if self.conn and self.cur:
            self.cur.close()
            self.conn.close()

    @contextmanager
    def session(self):
        self.__init_conn_handle()
        yield
        self.__close_conn()


class SQLServerExecutor(BaseExecutor):
    """SQLServer executor implementation."""

    def __init__(self, database, user, password, host, port, schema):
        """Init SQLServer executor."""
        super().__init__(database, user, password, host, port, schema)
        if not PYODBC_IMPORTED:
            raise ImportError("pyodbc package is not installed. Please install it with 'pip install pyodbc'")
        self.conn = None
        
        # Try different SQL Server driver names (in order of preference)
        self.drivers = [
            'ODBC Driver 17 for SQL Server',  # Latest Microsoft driver
            'ODBC Driver 13 for SQL Server',  # Older Microsoft driver
            'SQL Server',                    # Default/generic name
            'SQL Server Native Client 11.0',  # SQL 2012 native client
            'SQL Server Native Client 10.0'   # SQL 2008 native client
        ]
        self.schema = schema
        
        # Check if we're using Windows Authentication
        self.use_trusted_connection = (user is None)
        
        # Handle SQL Server Express instance format
        # Remove any parentheses from the host name for command line compatibility
        if host.startswith('(') and host.endswith(')'):
            host = host[1:-1]
            
        # If hostname contains backslash, it's likely a named instance
        if '\\' in host:
            # No need to specify port for named instances
            print(f"Detected named instance format: {host}")
            self.instance_name = host
            self.port = None
        # Handle default instance running on default port
        else:
            self.instance_name = host
        
        # Connect immediately during initialization
        self.connect()

    def connect(self):
        """Connect to SQLServer."""
        # SQL Server connection methods to try
        connection_methods = []
        
        # Detect if we're dealing with LocalDB
        is_localdb = 'localdb' in self.instance_name.lower()
        
        # Add LocalDB specific connection strings first if it's a LocalDB instance
        if is_localdb:
            # For LocalDB, Windows Authentication is typically used
            print("Detected LocalDB instance, trying specific LocalDB connection strings...")
            
            # Try various LocalDB connection formats with Windows Authentication
            localdb_methods = [
                # Method 1: Standard LocalDB format with parentheses
                {
                    'conn_str': f'DRIVER={{ODBC Driver 17 for SQL Server}};Server=(localdb)\\MSSQLLocalDB;Database={self.dbname};Trusted_Connection=yes;',
                    'description': "LocalDB standard format with ODBC Driver 17"
                },
                # Method 2: Standard LocalDB format without parentheses
                {
                    'conn_str': f'DRIVER={{ODBC Driver 17 for SQL Server}};Server=localdb\\MSSQLLocalDB;Database={self.dbname};Trusted_Connection=yes;',
                    'description': "LocalDB without parentheses with ODBC Driver 17"
                },
                # Method 3: LocalDB with auto-detection
                {
                    'conn_str': f'DRIVER={{ODBC Driver 17 for SQL Server}};Server=(LocalDB)\\MSSQLLocalDB;AttachDBFileName={self.dbname};Integrated Security=True;',
                    'description': "LocalDB with database attachment and ODBC Driver 17"
                },
                # Method 4: Using the SQL Server driver
                {
                    'conn_str': f'DRIVER={{SQL Server}};Server=(localdb)\\MSSQLLocalDB;Database={self.dbname};Trusted_Connection=yes;',
                    'description': "LocalDB with SQL Server driver"
                },
                # Method 5: With explicit Current User
                {
                    'conn_str': f'DRIVER={{ODBC Driver 17 for SQL Server}};Server=(localdb)\\MSSQLLocalDB;Database={self.dbname};Trusted_Connection=yes;',
                    'description': "LocalDB with explicit Trusted_Connection"
                }
            ]
            
            connection_methods.extend(localdb_methods)
        
        # Detect if we're dealing with a named instance (contains backslash)
        is_named_instance = '\\' in self.instance_name
        
        # 1. For named instances (like DESKTOP\SQLEXPRESS)
        if is_named_instance:
            if self.use_trusted_connection:
                # With Windows Authentication
                for driver in self.drivers:
                    connection_methods.append({
                        'driver': driver,
                        'conn_str': f'DRIVER={{{driver}}};SERVER={self.instance_name};DATABASE={self.dbname};Trusted_Connection=yes;',
                        'description': f"{driver} - Named instance with Windows Authentication"
                    })
            else:
                # With SQL Authentication
                for driver in self.drivers:
                    connection_methods.append({
                        'driver': driver,
                        'conn_str': f'DRIVER={{{driver}}};SERVER={self.instance_name};DATABASE={self.dbname};UID={self.user};PWD={self.password}',
                        'description': f"{driver} - Named instance with SQL Authentication"
                    })
        
        # Rest of the connection methods
        # ... existing code ...
        
        # Try all connection methods
        for method in connection_methods:
            try:
                print(f"Trying: {method['description']}")
                conn_str = method.get('conn_str', '')
                self.conn = pyodbc.connect(conn_str)
                self.conn.autocommit = True
                print(f"✓ CONNECTION SUCCESSFUL: {method['description']}")
                
                # Log driver and connection version info
                cursor = self.conn.cursor()
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                print(f"SQL Server Version: {version[:50]}...")
                
                # Test if the database exists and can be accessed
                try:
                    cursor.execute(f"USE {self.dbname}")
                    cursor.execute("SELECT DB_NAME()")
                    db_name = cursor.fetchone()[0]
                    print(f"Connected to database: {db_name}")
                except pyodbc.Error as e:
                    print(f"Warning: Database '{self.dbname}' may not exist or is not accessible: {str(e)}")
                
                return True
            except pyodbc.Error as e:
                print(f"  × Connection failed: {str(e)[:100]}")
                continue
            except Exception as e:
                print(f"  × Unexpected error: {str(e)[:100]}")
                continue

        # Display detailed error information
        print("\n=== SQL SERVER CONNECTION TROUBLESHOOTING ===")
        print(f"Failed to connect to LocalDB instance: {self.instance_name}")
        print(f"Database: {self.dbname}")
        print("\nROOT CAUSE ANALYSIS:")
        print("Based on error messages, you are likely experiencing one of these issues:")
        print("1. LocalDB instance is not running or not properly installed")
        print("2. The database you're trying to access doesn't exist")
        print("3. Windows Authentication configuration issue")
        
        print("\nRECOMMENDED SOLUTIONS:")
        print("1. Verify LocalDB is installed and running:")
        print("   > sqllocaldb info")
        print("   > sqllocaldb start MSSQLLocalDB")
        
        print("\n2. Create the database if it doesn't exist:")
        print("   - Connect to LocalDB with SSMS using: (localdb)\\MSSQLLocalDB")
        print("   - Right-click on 'Databases' folder and select 'New Database'")
        print(f"   - Create a database named '{self.dbname}'")
        
        print("\n3. Verify workload.sql file contains valid SQL queries")
        print("   - Check the file exists and contains SQL SELECT statements")
        
        return False

    def execute_sql(self, sql):
        """Execute SQL in SQLServer."""
        if self.conn is None:
            if not self.connect():
                error_msg = "Cannot execute SQL: No connection to SQL Server"
                print(error_msg)
                logging.error(error_msg)
                return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            if cursor.description:
                results = cursor.fetchall()
                return results
            return []
        except pyodbc.Error as e:
            error_msg = f"Failed to execute SQL: {sql}, error: {e}"
            print(error_msg)
            logging.error(error_msg)
            return []
        except Exception as e:
            error_msg = f"Unexpected error executing SQL: {e}"
            print(error_msg)
            logging.error(error_msg)
            return []

    def execute_sqls(self, sqls):
        """Execute SQLs in SQLServer."""
        results = []
        for sql in sqls:
            result = self.execute_sql(sql)
            if result:
                results.extend(result)
        return results

    def cancel(self):
        """Cancel the executing SQLs."""
        # Not fully implemented for SQL Server
        pass

    def get_schema(self):
        """Get schema."""
        return self.schema

    def close(self):
        """Close the connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    @contextmanager
    def session(self):
        """Context manager for database session."""
        connected = False
        if self.conn is None:
            connected = self.connect()
        
        try:
            yield
        finally:
            if connected:
                self.close()
