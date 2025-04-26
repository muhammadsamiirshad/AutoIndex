

import os
import sys

try:
    from dbmind.components.index_advisor import main
except ImportError:
    libpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    sys.path.append(libpath)
    try:
        # Check if we should use SQL Server version with default parameters
        if '--sqlserver' in sys.argv:
            from index_advisor_sqlserver import main
            # Remove the --sqlserver flag from args before passing to main
            sys.argv.remove('--sqlserver')
            
            # Apply default values if placeholders are provided
            args_copy = sys.argv[:]
            
            # Check for placeholder values and replace with defaults
            if '<db_port>' in args_copy:
                args_copy[args_copy.index('<db_port>')] = '1433'
            
            if '<database>' in args_copy:
                args_copy[args_copy.index('<database>')] = 'master'
                
            if '<workload_file>' in args_copy:
                # Use the sample workload.sql in the current directory
                workload_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'workload.sql')
                args_copy[args_copy.index('<workload_file>')] = workload_path
            
            # Check for --schema parameter
            if '--schema' in args_copy:
                schema_index = args_copy.index('--schema')
                if schema_index + 1 < len(args_copy) and args_copy[schema_index + 1] == '<schema_name>':
                    args_copy[schema_index + 1] = 'dbo'
            else:
                args_copy.extend(['--schema', 'dbo'])
                
            # Check for --db-host parameter
            if '--db-host' in args_copy:
                host_index = args_copy.index('--db-host')
                if host_index + 1 < len(args_copy) and args_copy[host_index + 1] == '<host>':
                    args_copy[host_index + 1] = 'localhost'
            else:
                args_copy.extend(['--db-host', 'localhost'])
                
            # Check for -U parameter
            if '-U' in args_copy:
                user_index = args_copy.index('-U')
                if user_index + 1 < len(args_copy) and args_copy[user_index + 1] == '<username>':
                    args_copy[user_index + 1] = 'sa'
            elif '--db-user' in args_copy:
                user_index = args_copy.index('--db-user')
                if user_index + 1 < len(args_copy) and args_copy[user_index + 1] == '<username>':
                    args_copy[user_index + 1] = 'sa'
            else:
                args_copy.extend(['-U', 'sa'])
                
            main(args_copy[1:])
        else:
            from index_advisor_workload import main
            main(sys.argv[1:])
    except ImportError as e:
        print(f"Error importing module: {e}")
        print("If you're trying to use SQL Server, make sure pyodbc is installed:")
        print("pip install pyodbc")
        sys.exit(1)
