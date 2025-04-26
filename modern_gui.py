#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import threading
import time
import re
import glob
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QFileDialog, QFrame, QGroupBox,
    QProgressBar, QStatusBar, QMessageBox, QRadioButton, QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QTextCursor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QDialog

# Import our custom modules
from gui_theme import Theme, apply_theme, get_stylesheet  
from gui_icons import get_app_icon, draw_index_icon

# Project configuration auto-detection
class ProjectConfig:
    """Auto-detect project configuration"""
    
    @staticmethod
    def get_default_server():
        """Get default SQL Server from project files"""
        try:
            # First try to import directly from the module
            try:
                import direct_index_recommendations
                server_match = re.search(r'Server=([^;]+)', direct_index_recommendations.conn_str, re.IGNORECASE)
                if server_match:
                    return server_match.group(1)
            except (ImportError, AttributeError):
                pass
            
            # If that fails, try reading from the file
            with open('direct_index_recommendations.py', 'r') as f:
                content = f.read()
                
                # First look for direct definition in create_sql_connection_string
                server_match = re.search(r'server=r[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE)
                if server_match:
                    return server_match.group(1)
                    
                # Fall back to searching for Server= in connection string
                server_match = re.search(r'Server=([^;]+)', content, re.IGNORECASE)
                if server_match:
                    return server_match.group(1)
                    
            return "(localdb)\\MSSQLLocalDB"  # Default value
        except:
            return "(localdb)\\MSSQLLocalDB"
    
    @staticmethod
    def get_default_database():
        """Get default database from project files"""
        try:
            # First try to import directly from the module
            try:
                import direct_index_recommendations
                db_match = re.search(r'Database=([^;]+)', direct_index_recommendations.conn_str, re.IGNORECASE)
                if db_match:
                    return db_match.group(1)
            except (ImportError, AttributeError):
                pass
                
            # If that fails, try reading from the file
            with open('direct_index_recommendations.py', 'r') as f:
                content = f.read()
                
                # First look for direct definition in create_sql_connection_string
                db_match = re.search(r'database=[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE)
                if db_match:
                    return db_match.group(1)
                
                # Also check for the current_database_name variable which might be set directly
                db_match = re.search(r'current_database_name\s*=\s*[\'"]([^\'"]+)[\'"]', content, re.IGNORECASE)
                if db_match:
                    return db_match.group(1)
                
                # Fall back to searching for Database= in connection string
                db_match = re.search(r'Database=([^;]+)', content, re.IGNORECASE)
                if db_match:
                    return db_match.group(1)
                    
            return "MedicalStorePOS"  # Default value
        except:
            return "MedicalStorePOS"
            
    @staticmethod
    def get_default_workload():
        """Get default workload file path"""
        # Look for workload.sql in the current directory first
        if os.path.exists('workload.sql'):
            return os.path.abspath('workload.sql')
        
        # Look for any SQL files in the current directory
        sql_files = glob.glob('*.sql')
        if sql_files:
            return os.path.abspath(sql_files[0])
        
        return ""
    
    @staticmethod
    def get_default_schema():
        """Get default schema from workload file"""
        try:
            with open('workload.sql', 'r') as f:
                content = f.read()
                # Look for schema mentions in queries
                matches = re.findall(r'FROM\s+(\w+)\.', content)
                if matches:
                    # Return the most common schema
                    from collections import Counter
                    return Counter(matches).most_common(1)[0][0]
            return "dbo"  # Default schema
        except:
            return "dbo"

    @staticmethod
    def get_table_list():
        """Get list of tables used in the workload"""
        tables = []
        try:
            with open('workload.sql', 'r') as f:
                content = f.read()
                # Extract tables from FROM and JOIN clauses
                matches = re.findall(r'FROM\s+(\w+\.\w+)|JOIN\s+(\w+\.\w+)', content)
                for match in matches:
                    if match[0]:
                        tables.append(match[0])
                    if match[1]:
                        tables.append(match[1])
            return list(set(tables))  # Return unique tables
        except:
            return []

class AnalysisThread(QThread):
    """Background thread to run analysis without blocking UI"""
    analysis_complete = pyqtSignal(dict, str)
    progress_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, connection_params, workload_file, options):
        super().__init__()
        self.connection_params = connection_params
        self.workload_file = workload_file
        self.options = options
        
    def run(self):
        try:
            self.progress_update.emit("Starting analysis...")
            
            # Create database connection
            self.progress_update.emit("Connecting to database...")
            
            conn_params = self.connection_params
            
            # Import SQL Server specific modules
            try:
                from direct_index_recommendations import get_direct_recommendations
                from utils import create_sql_connection_string
                
                # Use the shared connection string helper to maintain consistency
                conn_str = create_sql_connection_string(
                    server=conn_params['server'],
                    database=conn_params['database'],
                    auth_type=conn_params['auth_type'],
                    username=conn_params.get('username', ''),
                    password=conn_params.get('password', '')
                )
                
                # Set the connection string in the module
                import direct_index_recommendations
                direct_index_recommendations.conn_str = conn_str
                
                # Call the main function with the workload file
                self.progress_update.emit("Starting SQL Server index analysis...")
                self.progress_update.emit(f"Processing workload file: {os.path.basename(self.workload_file)}")
                self.progress_update.emit(f"Tables found: {', '.join(ProjectConfig.get_table_list())}")
                
                # Redirect stdout to capture output
                import io
                from contextlib import redirect_stdout
                
                output_buffer = io.StringIO()
                success = False
                
                with redirect_stdout(output_buffer):
                    # Call the analysis function
                    success = get_direct_recommendations(self.workload_file)
                
                output = output_buffer.getvalue()
                
                # Process the results (empty dict for now since we're capturing output directly)
                results = {"success": success}
                
                self.analysis_complete.emit(results, output)
                
            except ImportError:
                # Fall back to index_advisor_sqlserver if direct_index_recommendations is not available
                import index_advisor_sqlserver
                from index_advisor_sqlserver import main as sqlserver_main
                
                # Build arguments list
                args = [
                    str(conn_params.get('port', '1433')),
                    conn_params['database'],
                    '--db-host', conn_params['server'],
                    '--schema', conn_params.get('schema', 'dbo'),
                    '--max-index-num', self.options['max_indexes'],
                    '--max-index-columns', self.options['max_columns'],
                    '--min-improved-rate', self.options['min_improved'],
                ]
                
                if conn_params['auth_type'] == 'sql':
                    args.extend(['-U', conn_params['username']])
                    # Password will be handled via environment variable
                
                # Add workload file as last parameter
                args.append(self.workload_file)
                
                # Set password environment variable
                if conn_params['auth_type'] == 'sql':
                    os.environ['PGPASSWORD'] = conn_params['password']
                
                # Redirect stdout to capture output
                import io
                from contextlib import redirect_stdout
                
                output_buffer = io.StringIO()
                results = None
                
                with redirect_stdout(output_buffer):
                    # Call the analysis function
                    results = sqlserver_main(args)
                
                output = output_buffer.getvalue()
                
                self.analysis_complete.emit(results or {}, output)
                
        except Exception as e:
            self.error_occurred.emit(str(e))
            import traceback
            print(traceback.format_exc())

class SimpleAutoIndexApp(QMainWindow):
    """Simple and user-friendly AutoIndex application"""
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SQL Server Index Advisor")
        self.setWindowIcon(get_app_icon())
        self.setMinimumSize(1200, 700)  # Wider window to accommodate side-by-side layout
        
        # Set up the central widget with a horizontal layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main horizontal layout to split the UI into two columns
        self.horizontal_layout = QHBoxLayout(self.central_widget)
        self.horizontal_layout.setContentsMargins(15, 15, 15, 15)
        self.horizontal_layout.setSpacing(15)
        
        # LEFT SIDE - Inputs
        self.left_column = QWidget()
        self.left_layout = QVBoxLayout(self.left_column)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(20)
        
        # Create header with title and description - simple, clean style
        title_label = QLabel("SQL Server Index Advisor")
        title_label.setStyleSheet("font-size: 24pt; font-weight: bold; color: #0078d7;")
        title_label.setAlignment(Qt.AlignCenter)
        
        desc_label = QLabel("Find the optimal database indexes for your SQL Server workload")
        desc_label.setStyleSheet("font-size: 14pt; color: #444444;")
        desc_label.setAlignment(Qt.AlignCenter)
        
        self.left_layout.addWidget(title_label)
        self.left_layout.addWidget(desc_label)
        
        # Database Connection Section
        db_group = QGroupBox("SQL Server Connection")
        db_group.setStyleSheet("QGroupBox { font-size: 12pt; font-weight: bold; padding-top: 15px; }")
        db_layout = QGridLayout(db_group)
        db_layout.setContentsMargins(20, 30, 20, 20)
        db_layout.setVerticalSpacing(15)
        db_layout.setHorizontalSpacing(10)
        
        # Server
        server_label = QLabel("Server:")
        server_label.setMinimumWidth(80)
        # Auto-fill with default server from project
        self.server_input = QLineEdit(ProjectConfig.get_default_server())
        self.server_input.setMinimumHeight(25)
        
        # Database name
        db_name_label = QLabel("Database:")
        db_name_label.setMinimumWidth(80)
        # Auto-fill with default database from project
        self.db_name_input = QLineEdit(ProjectConfig.get_default_database())
        self.db_name_input.setMinimumHeight(25)
        
        # Use grid layout to align labels and fields
        db_layout.addWidget(server_label, 0, 0)
        db_layout.addWidget(self.server_input, 0, 1)
        db_layout.addWidget(db_name_label, 1, 0)
        db_layout.addWidget(self.db_name_input, 1, 1)
        
        # Authentication
        auth_layout = QHBoxLayout()
        auth_layout.setContentsMargins(0, 10, 0, 10)
        
        self.windows_auth = QRadioButton("Windows Authentication")
        self.windows_auth.setChecked(True)
        self.sql_auth = QRadioButton("SQL Server Authentication")
        auth_layout.addWidget(self.windows_auth)
        auth_layout.addWidget(self.sql_auth)
        auth_layout.addStretch(1)
        
        db_layout.addLayout(auth_layout, 2, 0, 1, 2)
        
        # Username/Password (initially hidden)
        self.auth_frame = QFrame()
        auth_fields_layout = QGridLayout(self.auth_frame)
        auth_fields_layout.setContentsMargins(0, 0, 0, 0)
        auth_fields_layout.setVerticalSpacing(15)
        
        user_label = QLabel("Username:")
        user_label.setMinimumWidth(80)
        self.user_input = QLineEdit()
        self.user_input.setMinimumHeight(25)
        
        pass_label = QLabel("Password:")
        pass_label.setMinimumWidth(80)
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setMinimumHeight(25)
        
        auth_fields_layout.addWidget(user_label, 0, 0)
        auth_fields_layout.addWidget(self.user_input, 0, 1)
        auth_fields_layout.addWidget(pass_label, 1, 0)
        auth_fields_layout.addWidget(self.pass_input, 1, 1)
        
        db_layout.addWidget(self.auth_frame, 3, 0, 1, 2)
        self.auth_frame.setVisible(False)
        
        # Connect signals for auth toggle
        self.sql_auth.toggled.connect(self.toggle_auth_fields)
        
        # Test connection button
        self.test_conn_btn = QPushButton("Test Connection")
        self.test_conn_btn.setStyleSheet(
            "QPushButton { background-color: #0078d7; color: white; padding: 8px 16px; }"
        )
        self.test_conn_btn.setMinimumHeight(30)
        self.test_conn_btn.setFixedWidth(200)
        self.test_conn_btn.clicked.connect(self.test_connection)
        
        # Center the button
        test_btn_layout = QHBoxLayout()
        test_btn_layout.addStretch(1)
        test_btn_layout.addWidget(self.test_conn_btn)
        test_btn_layout.addStretch(1)
        db_layout.addLayout(test_btn_layout, 4, 0, 1, 2)
        
        self.left_layout.addWidget(db_group)
        
        # Workload Section
        workload_group = QGroupBox("SQL Workload")
        workload_group.setStyleSheet("QGroupBox { font-size: 12pt; font-weight: bold; padding-top: 15px; }")
        workload_layout = QVBoxLayout(workload_group)
        workload_layout.setContentsMargins(20, 30, 20, 20)
        workload_layout.setSpacing(15)
        
        # File selection
        file_layout = QHBoxLayout()
        file_label = QLabel("SQL File:")
        file_label.setMinimumWidth(80)
        # Auto-fill with default workload file from project
        self.file_path = QLineEdit(ProjectConfig.get_default_workload())
        self.file_path.setMinimumHeight(25)
        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_btn)
        workload_layout.addLayout(file_layout)
        
        # Options section
        options_frame = QFrame()
        options_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 5px;")
        options_layout = QGridLayout(options_frame)
        options_layout.setContentsMargins(15, 15, 15, 15)
        options_layout.setVerticalSpacing(10)
        options_layout.setHorizontalSpacing(15)
        
        # Option title
        options_title = QLabel("Analysis Options")
        options_title.setStyleSheet("font-weight: bold;")
        options_layout.addWidget(options_title, 0, 0, 1, 6)
        
        # Max Indexes option
        max_indexes_label = QLabel("Max Indexes:")
        self.max_indexes = QLineEdit("10")
        self.max_indexes.setFixedWidth(60)
        options_layout.addWidget(max_indexes_label, 1, 0)
        options_layout.addWidget(self.max_indexes, 1, 1)
        
        # Max Columns option
        max_cols_label = QLabel("Max Columns:")
        self.max_columns = QLineEdit("3")
        self.max_columns.setFixedWidth(60)
        options_layout.addWidget(max_cols_label, 1, 2)
        options_layout.addWidget(self.max_columns, 1, 3)
        
        # Min Improvement option
        min_improved_label = QLabel("Min Improvement:")
        self.min_improved = QLineEdit("0.1")
        self.min_improved.setFixedWidth(60)
        options_layout.addWidget(min_improved_label, 1, 4)
        options_layout.addWidget(self.min_improved, 1, 5)
        
        workload_layout.addWidget(options_frame)
        
        # Analyze Button
        self.analyze_btn = QPushButton("Analyze Workload")
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.analyze_btn.setStyleSheet(
            "QPushButton { background-color: #0078d7; color: white; font-weight: bold; padding: 8px 16px; }"
        )
        self.analyze_btn.setMinimumHeight(35)
        self.analyze_btn.setFixedWidth(200)
        
        # Center analyze button
        analyze_layout = QHBoxLayout()
        analyze_layout.addStretch(1)
        analyze_layout.addWidget(self.analyze_btn)
        analyze_layout.addStretch(1)
        workload_layout.addLayout(analyze_layout)
        
        self.left_layout.addWidget(workload_group)
        
        # Add stretch to push everything to the top
        self.left_layout.addStretch(1)
        
        # RIGHT SIDE - Results
        self.right_column = QWidget()
        self.right_layout = QVBoxLayout(self.right_column)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(20)
        
        # Results Section - now taking the full right side
        results_group = QGroupBox("Results")
        results_group.setStyleSheet("QGroupBox { font-size: 12pt; font-weight: bold; padding-top: 15px; }")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(20, 30, 20, 20)
        results_layout.setSpacing(15)
        
        # Console output - now takes full height of right column
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))
        self.console.setStyleSheet("background-color: white; border: 1px solid #dcdcdc;")
        self.console.setMinimumHeight(500)  # Taller console for better results visibility
        results_layout.addWidget(self.console)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #dcdcdc; }")
        results_layout.addWidget(self.progress_bar)
        self.progress_bar.hide()
        
        # Export button
        btn_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export Results to SQL")
        self.export_btn.setStyleSheet(
            "QPushButton { background-color: #107C10; color: white; padding: 8px 16px; }"
        )
        self.export_btn.setMinimumHeight(35)
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addStretch(1)
        
        results_layout.addLayout(btn_layout)
        
        self.right_layout.addWidget(results_group)
        
        # Add the left and right columns to the main horizontal layout
        # Left side should take 40% of the space, right side 60%
        self.horizontal_layout.addWidget(self.left_column, 40)
        self.horizontal_layout.addWidget(self.right_column, 60)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Initialize data storage
        self.analysis_results = None
        self.recommended_indexes = []
        self.useless_indexes = []
        self.analysis_thread = None
        
        # Set up file logging
        self.setup_logging()
        self.log_message("Application started")
        
        # Welcome message
        self.append_console("Welcome to SQL Server Index Advisor")
        self.append_console(f"Database: {self.db_name_input.text()} on {self.server_input.text()}")
        
        if os.path.exists(self.file_path.text()):
            self.append_console(f"Workload file loaded: {os.path.basename(self.file_path.text())}")
            self.append_console("Ready to analyze. Click 'Analyze Workload' to start.")
        else:
            self.append_console("Please select a workload SQL file to analyze.")
            
        # Center the window on the screen
        self.center_on_screen()

    def center_on_screen(self):
        """Center the application window on the screen"""
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def append_console(self, text, level="normal"):
        """Append text to console with color based on level and improved formatting"""
        colors = {
            "normal": "#202020",
            "success": "#007800",
            "warning": "#FF8C00",
            "error": "#C80000",
            "highlight": "#0078d7"
        }
        
        # Format certain messages with better visual cues
        if level == "success" and ("completed" in text.lower() or "successful" in text.lower()):
            text = "✓ " + text
        elif level == "warning":
            text = "⚠ " + text
        elif level == "error":
            text = "❌ " + text
        elif "started" in text.lower() or "processing" in text.lower():
            level = "highlight"
            text = "➤ " + text
        
        color = colors.get(level, colors["normal"])
        self.console.setTextColor(QColor(color))
        self.console.append(text)
        
        # Scroll to bottom
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.console.setTextCursor(cursor)
        
        # Also write to log if it's important
        if level != "normal":
            self.log_message(text, level)

    def toggle_auth_fields(self, checked):
        """Show/hide SQL authentication fields based on radio button selection"""
        self.auth_frame.setVisible(checked)
        
        # Adjust the window layout to account for the newly visible/hidden elements
        if checked:
            self.append_console("SQL Server Authentication selected", "normal")
        else:
            self.append_console("Windows Authentication selected", "normal")
            
        # Clear the username/password fields when hiding them (for security)
        if not checked:
            self.user_input.clear()
            self.pass_input.clear()

    def browse_file(self):
        """Open file dialog to select SQL workload file"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select SQL Workload File", "", "SQL Files (*.sql);;All Files (*.*)"
        )
        if file_name:
            self.file_path.setText(file_name)
            self.append_console(f"Workload file selected: {os.path.basename(file_name)}", "normal")
            
            # Check if the file exists and has content
            if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
                # Try to detect tables in the selected file
                tables = []
                try:
                    with open(file_name, 'r', errors='ignore') as f:
                        content = f.read()
                        # Extract tables from FROM and JOIN clauses
                        matches = re.findall(r'FROM\s+(\w+\.\w+)|JOIN\s+(\w+\.\w+)', content)
                        for match in matches:
                            if match[0]:
                                tables.append(match[0])
                            if match[1]:
                                tables.append(match[1])
                    tables = list(set(tables))  # Remove duplicates
                    
                    if tables:
                        self.append_console(f"Detected tables: {', '.join(tables)}", "highlight")
                except Exception as e:
                    self.log_message(f"Error detecting tables: {str(e)}", "error")

    def export_results(self):
        """Export results to SQL file with improved handling for raw output"""
        # Check if we have any content to export
        if not self.recommended_indexes and not self.useless_indexes:
            # Get console text to see if we have any output at all
            console_text = self.console.toPlainText().strip()
            
            if not console_text:
                QMessageBox.warning(self, "No Results", "There are no results to export.")
                return
            
            # We have console text but no processed indexes, export raw output without asking
            self.export_raw_output()
            return
                
        # We have processed results, proceed with normal export
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "SQL Files (*.sql);;Text Files (*.txt);;All Files (*.*)"
        )
        
        if not file_name:
            return
            
        try:
            with open(file_name, 'w') as f:
                # Write header with improved formatting
                f.write("-- ========================================================\n")
                f.write("-- SQL Server Index Advisor Recommendations\n")
                f.write(f"-- Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: {self.db_name_input.text()} on {self.server_input.text()}\n")
                f.write(f"-- Workload file: {os.path.basename(self.file_path.text())}\n")
                f.write("-- ========================================================\n\n")
                
                # Write recommended indexes
                if self.recommended_indexes:
                    f.write("-- ==================== RECOMMENDED INDEXES ====================\n")
                    f.write(f"-- Total recommended indexes: {len(self.recommended_indexes)}\n\n")
                    for i, index in enumerate(self.recommended_indexes):
                        f.write(f"-- Index {i+1}: {index.get('table', 'Unknown table')}\n")
                        if 'improvement' in index and index['improvement']:
                            f.write(f"-- Estimated improvement: {index['improvement']:.2f}%\n")
                        f.write(f"{index['statement']}\n\n")
                
                # Write useless indexes
                if self.useless_indexes:
                    f.write("-- ==================== USELESS INDEXES ====================\n")
                    f.write(f"-- Total useless indexes: {len(self.useless_indexes)}\n")
                    f.write("-- Consider dropping these indexes to improve performance\n\n")
                    for i, index in enumerate(self.useless_indexes):
                        f.write(f"-- Index {i+1}: {index.get('table', 'Unknown table')}\n")
                        f.write(f"{index['statement']}\n\n")
                
            self.append_console(f"Results successfully exported to {file_name}", "success")
            self.log_message(f"Results exported to {file_name}")
            self.status_bar.showMessage(f"Results saved to {file_name}", 5000)  # Show for 5 seconds
            
            # Show success message
            QMessageBox.information(self, "Export Successful", f"Results were successfully exported to:\n{file_name}")
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.append_console(error_msg, "error")
            self.log_message(error_msg, "error")
            self.status_bar.showMessage("Export failed")
            QMessageBox.critical(self, "Export Error", error_msg)
            
    def export_raw_output(self):
        """Export raw console output to a file"""
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Raw Output", "", "SQL Files (*.sql);;Text Files (*.txt);;All Files (*.*)"
        )
        
        if not file_name:
            return
            
        try:
            with open(file_name, 'w') as f:
                # Write header
                f.write("-- ========================================================\n")
                f.write("-- SQL Server Index Advisor - Raw Analysis Output\n")
                f.write(f"-- Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Database: {self.db_name_input.text()} on {self.server_input.text()}\n")
                f.write(f"-- Workload file: {os.path.basename(self.file_path.text())}\n")
                f.write("-- ========================================================\n\n")
                
                # Write raw console output
                f.write("-- ==================== RAW ANALYSIS OUTPUT ====================\n")
                f.write(self.console.toPlainText())
                        
            self.append_console(f"Raw output successfully exported to {file_name}", "success")
            self.log_message(f"Raw output exported to {file_name}")
            self.status_bar.showMessage(f"Raw output saved to {file_name}", 5000)
            
            # Show success message
            QMessageBox.information(self, "Export Successful", f"Raw output was successfully exported to:\n{file_name}")
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.append_console(error_msg, "error")
            self.log_message(error_msg, "error")
            self.status_bar.showMessage("Export failed")
            QMessageBox.critical(self, "Export Error", error_msg)

    def test_connection(self):
        """Test the database connection with improved feedback"""
        try:
            # Get connection parameters
            conn_params = self.get_connection_params()
            
            self.append_console(f"Testing connection to {conn_params['server']}...", "normal")
            self.log_message(f"Testing connection to {conn_params['server']}")
            
            # Show a temporary status in status bar
            self.status_bar.showMessage("Connecting to database...")
            
            # Temporarily disable the test button and change its text
            self.test_conn_btn.setEnabled(False)
            self.test_conn_btn.setText("Connecting...")
            QApplication.processEvents()  # Update the UI
            
            # Import pyodbc for SQL Server connection
            try:
                import pyodbc
                from utils import create_sql_connection_string
                
                # Use the shared connection string helper to maintain consistency
                conn_str = create_sql_connection_string(
                    server=conn_params['server'],
                    database=conn_params['database'],
                    auth_type=conn_params['auth_type'],
                    username=conn_params.get('username', ''),
                    password=conn_params.get('password', '')
                )
                
                # Test connection
                self.log_message(f"Attempting connection with string: {conn_str.replace(conn_params.get('password', ''), '****')}")
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                conn.close()
                
                # Calculate connection time
                self.append_console("Connection successful!", "success")
                
                # Format the version string for better readability
                version_lines = version.split('\n')
                version_formatted = version_lines[0]  # Just take the first line for brevity
                self.append_console(f"Server version: {version_formatted}", "normal")
                
                self.log_message("Connection successful")
                
                self.status_bar.showMessage("Connection successful!", 5000)
                
                # Show success dialog with more details
                QMessageBox.information(self, "Connection Successful", 
                    f"Successfully connected to {conn_params['server']}.\n\n" + 
                    f"Database: {conn_params['database']}\n" +
                    f"Server version: {version_formatted}"
                )
                
                return True
                
            except ImportError:
                error_msg = "ODBC driver for SQL Server not found. Please install pyodbc package."
                self.append_console(error_msg, "error")
                self.log_message(error_msg, "error")
                QMessageBox.critical(self, "Connection Error", error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            self.append_console(error_msg, "error")
            self.log_message(error_msg, "error")
            self.status_bar.showMessage("Connection failed")
            
            # Show detailed error message with driver check
            try:
                import pyodbc
                drivers = pyodbc.drivers()
                if not any('SQL Server' in driver for driver in drivers):
                    detail = "No SQL Server ODBC drivers found. Please install SQL Server ODBC Driver."
                else:
                    detail = f"Available drivers: {', '.join(drivers)}"
                
                error_detail = f"{error_msg}\n\n{detail}"
                
            except ImportError:
                error_detail = f"{error_msg}\n\nPyODBC is not installed. Please install it with: pip install pyodbc"
            
            QMessageBox.critical(self, "Connection Error", error_detail)
            return False
        finally:
            # Re-enable the test button and restore its text
            self.test_conn_btn.setEnabled(True)
            self.test_conn_btn.setText("Test Connection")

    def start_analysis(self):
        """Start the workload analysis"""
        try:
            # Clear previous output
            self.console.clear()
            
            # Validate inputs
            conn_params = self.get_connection_params()
            options = self.get_options()
            workload_file = self.file_path.text()
            
            if not conn_params['server']:
                raise ValueError("Server name is required")
                
            if not conn_params['database']:
                raise ValueError("Database name is required")
                
            if conn_params['auth_type'] == 'sql' and not conn_params['username']:
                raise ValueError("Username is required for SQL authentication")
                
            if not workload_file:
                raise ValueError("SQL workload file is required")
                
            if not os.path.exists(workload_file):
                raise ValueError(f"SQL workload file not found: {workload_file}")
                
            # Test connection first
            if not self.test_connection():
                self.append_console("Cannot proceed without database connection.", "error")
                return
            
            # Disable the analyze button and show progress
            self.analyze_btn.setEnabled(False)
            self.progress_bar.setRange(0, 0)  # Indeterminate mode
            self.progress_bar.show()
            self.status_bar.showMessage("Analysis in progress...")
            
            # Show initial message
            self.append_console(f"Starting analysis of workload file: {workload_file}", "normal")
            self.append_console(f"Database: {conn_params['server']} / {conn_params['database']}", "normal")
            self.append_console("Please wait, this may take a few minutes...", "normal")
            
            # Start analysis thread
            self.analysis_thread = AnalysisThread(conn_params, workload_file, options)
            self.analysis_thread.progress_update.connect(self.append_console)
            self.analysis_thread.analysis_complete.connect(self.analysis_finished)
            self.analysis_thread.error_occurred.connect(self.analysis_error)
            self.analysis_thread.start()
            
            self.log_message(f"Analysis started for {workload_file}")
            
        except Exception as e:
            error_msg = f"Error starting analysis: {str(e)}"
            self.append_console(error_msg, "error")
            self.log_message(error_msg, "error")
            self.status_bar.showMessage("Error starting analysis")
            QMessageBox.critical(self, "Error", error_msg)
            self.analyze_btn.setEnabled(True)
            self.progress_bar.hide()

    def get_connection_params(self):
        """Get database connection parameters from the UI"""
        params = {}
        
        # Always SQL Server
        params['type'] = 'sqlserver'
        
        # Get connection details
        params['server'] = self.server_input.text()
        params['database'] = self.db_name_input.text()
        
        # Get authentication type
        if self.windows_auth.isChecked():
            params['auth_type'] = 'windows'
            params['username'] = ''
            params['password'] = ''
        else:
            params['auth_type'] = 'sql'
            params['username'] = self.user_input.text()
            params['password'] = self.pass_input.text()
        
        return params
    
    def get_options(self):
        """Get analysis options from the UI"""
        return {
            'max_indexes': self.max_indexes.text(),
            'max_columns': self.max_columns.text(),
            'min_improved': self.min_improved.text()
        }

    def setup_logging(self):
        """Set up simple file logging for the application"""
        import logging
        logging.basicConfig(
            filename='modern_gui.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AutoIndex')
    
    def log_message(self, message, level='info'):
        """Log a message to the log file"""
        if hasattr(self, 'logger'):
            if level == 'info':
                self.logger.info(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'warning':
                self.logger.warning(message)
    
    def analysis_finished(self, results, output):
        """Handle analysis completion"""
        # Hide progress bar
        self.progress_bar.hide()
        
        # Store results
        self.analysis_results = results
        self.log_message("Analysis completed")
        
        # Extract recommended and useless indexes
        if isinstance(results, tuple) and len(results) >= 3:
            detail_info, recommended, useless = results
            
            # Process recommended indexes
            if detail_info and 'recommendIndexes' in detail_info:
                for index in detail_info['recommendIndexes']:
                    self.recommended_indexes.append({
                        'table': index.get('tbName', ''),
                        'columns': index.get('columns', ''),
                        'type': index.get('index_type', ''),
                        'improvement': float(index.get('workloadOptimized', 0)),
                        'statement': index.get('statement', '')
                    })
            
            # Process useless indexes
            if detail_info and 'uselessIndexes' in detail_info:
                for index in detail_info['uselessIndexes']:
                    self.useless_indexes.append({
                        'table': index.get('tbName', ''),
                        'columns': index.get('columns', ''),
                        'type': index.get('type', ''),
                        'statement': index.get('statement', '')
                    })
        else:
            # Try to parse results from text output
            self.recommended_indexes, self.useless_indexes = self.parse_results_from_text(output)
        
        # Display summary
        self.append_console("\nAnalysis completed successfully!", "success")
        self.append_console(f"Found {len(self.recommended_indexes)} recommended indexes", "normal")
        self.append_console(f"Found {len(self.useless_indexes)} useless indexes", "normal")
        
        # Show recommended indexes
        if self.recommended_indexes:
            self.append_console("\nRecommended Indexes:", "normal")
            for i, index in enumerate(self.recommended_indexes):
                self.append_console(f"{i+1}. Table: {index['table']}", "normal")
                self.append_console(f"   Columns: {index['columns']}", "normal")
                if 'improvement' in index and index['improvement']:
                    self.append_console(f"   Improvement: {index['improvement']:.2f}%", "normal")
                self.append_console(f"   SQL: {index['statement']}", "normal")
                self.append_console("", "normal")
        
        # Show useless indexes if any
        if self.useless_indexes:
            self.append_console("\nUseless Indexes (consider dropping):", "normal")
            for i, index in enumerate(self.useless_indexes):
                self.append_console(f"{i+1}. Table: {index['table']}", "normal")
                if index['columns']:
                    self.append_console(f"   Columns: {index['columns']}", "normal")
                self.append_console(f"   SQL: {index['statement']}", "normal")
                self.append_console("", "normal")
        
        # If no indexes found, but we have output
        if not self.recommended_indexes and not self.useless_indexes and output:
            self.append_console("\nRaw output from analysis:", "normal")
            self.append_console(output, "normal")
        
        # Re-enable analyze button and enable export
        self.analyze_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.status_bar.showMessage("Analysis completed successfully")
    
    def analysis_error(self, error_message):
        """Handle analysis error"""
        self.append_console(f"Error during analysis: {error_message}", "error")
        self.log_message(f"Analysis error: {error_message}", "error")
        self.progress_bar.hide()
        self.analyze_btn.setEnabled(True)
        self.status_bar.showMessage("Analysis failed")
        
        QMessageBox.critical(self, "Analysis Error", f"An error occurred during analysis:\n\n{error_message}")
        
    def parse_results_from_text(self, text):
        """Extract index recommendations from text output"""
        recommended = []
        useless = []
        
        # Process the text output to find CREATE INDEX statements
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Detect sections in the output
            if "RECOMMENDED INDEXES" in line or "recommend" in line.lower():
                current_section = "recommended"
                continue
            elif "USELESS INDEXES" in line or "useless" in line.lower():
                current_section = "useless"
                continue
                
            # Extract CREATE INDEX statements
            if line.lower().startswith("create index") and current_section == "recommended":
                index_info = self.parse_create_index(line)
                if index_info:
                    recommended.append(index_info)
                    
            # Extract DROP INDEX statements
            elif line.lower().startswith("drop index") and current_section == "useless":
                index_info = self.parse_drop_index(line)
                if index_info:
                    useless.append(index_info)
                    
        return recommended, useless
    
    def parse_create_index(self, statement):
        """Parse a CREATE INDEX statement to extract information"""
        try:
            # Very simple parsing - a more robust implementation would use SQL parsing
            import re
            pattern = r"CREATE INDEX\s+(\w+)\s+ON\s+([^\(]+)\(([^\)]+)\)"
            match = re.search(pattern, statement, re.IGNORECASE)
            
            if match:
                index_name = match.group(1)
                table = match.group(2).strip()
                columns = match.group(3).strip()
                
                return {
                    'table': table,
                    'columns': columns,
                    'type': 'btree',  # Default index type
                    'improvement': 0,  # Can't determine from statement alone
                    'statement': statement
                }
        except:
            pass
            
        return None
    
    def parse_drop_index(self, statement):
        """Parse a DROP INDEX statement to extract information"""
        try:
            import re
            pattern = r"DROP INDEX\s+([^;]+)"
            match = re.search(pattern, statement, re.IGNORECASE)
            
            if match:
                index_info = match.group(1).strip().split('.')
                
                return {
                    'table': index_info[-2] if len(index_info) > 1 else '',
                    'columns': '',  # Can't determine columns from drop statement
                    'type': '',
                    'statement': statement
                }
        except:
            pass
            
        return None

def main():
    # Create application
    app = QApplication(sys.argv)
    
    # Apply theme
    apply_theme(app, Theme.Light)
    app.setStyleSheet(get_stylesheet(Theme.Light))
    
    # Create and show window
    window = SimpleAutoIndexApp()
    window.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


