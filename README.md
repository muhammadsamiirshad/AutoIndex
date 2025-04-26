# AutoIndex: SQL Server Index Advisor

**AutoIndex** is an intelligent index recommendation system for database workloads. It analyzes SQL query patterns and database statistics to suggest optimal indexes that can significantly improve query performance.

## Overview

AutoIndex examines your SQL workload (a collection of SQL statements including SELECT, INSERT, DELETE, and UPDATE operations) and recommends the most beneficial indexes by:

1. Analyzing query patterns to identify potential indexing opportunities
2. Estimating the cost and benefit of candidate indexes
3. Considering both performance improvement and maintenance overhead
4. Providing recommendations with detailed improvement metrics

This version of AutoIndex has been optimized specifically for Microsoft SQL Server databases.

## Key Features

- **Direct Index Recommendations**: Leverages SQL Server's Dynamic Management Views (DMVs) to analyze query performance
- **Modern GUI Interface**: User-friendly interface to visualize index recommendations
- **Workload Analysis**: Processes batches of SQL queries to provide comprehensive recommendations
- **Cost-Benefit Analysis**: Calculates the estimated improvement for each recommended index
- **Redundant Index Detection**: Identifies existing indexes that are redundant or unused

## Components

- `direct_index_recommendations.py`: Core engine for SQL Server index analysis
- `modern_gui.py`: Graphical user interface for the application
- `utils.py`: Utility functions for database operations and analysis
- `table.py`: Table representation and metadata handling
- `workload.sql`: Sample SQL workload for testing

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Microsoft SQL Server (2016 or higher)
- Python packages: `pyodbc`, `tkinter` (for GUI)

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/AutoIndex.git
cd AutoIndex
```

2. Install required dependencies:
```
pip install -r requirements.txt
```

### Usage

#### Using the GUI

1. Start the GUI application:
```
python modern_gui.py
```

2. Enter your SQL Server connection details
3. Load a workload file or enter SQL queries directly
4. Click "Analyze" to generate index recommendations

#### Command Line Usage

For direct recommendations without the GUI:

```
python direct_index_recommendations.py --server [SERVER] --database [DATABASE] --workload [WORKLOAD_FILE]
```

### Sample Workload

The repository includes `workload.sql` with sample queries to demonstrate the functionality. You can use this as a template for creating your own workload files.

## Development

### Project Structure

- `executors/`: Database connection and execution handlers
- `direct_index_recommendations.py`: SQL Server-specific recommendation logic
- `modern_gui.py`: Tkinter-based GUI interface
- `utils.py`: Helper functions used across the project
- `table.py`: Table metadata management

## Academic Background

This project is based on research published in ICDE 2022:

```bibTeX
@inproceedings{autoindex2022,
    author    = {Xuanhe Zhou and Luyang Liu and Wenbo Li and Lianyuan Jin and Shifu Li and Tianqing Wang and Jianhua Feng},
    title     = {AutoIndex: An Incremental Index Management System for Dynamic Workloads},
    booktitle = {ICDE},
    year      = {2022}}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This project is adapted from the original [openGauss-DBMind Index Advisor](https://gitee.com/opengauss/openGauss-DBMind/tree/master/dbmind/components/index_advisor) and optimized for SQL Server databases.
