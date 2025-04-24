# JSON to CSV Converter

A FastAPI application that converts JSON data to CSV and displays it as a searchable, sortable HTML table.

## Features

- Convert JSON to CSV from file upload or direct text input
- Interactive HTML table with searching and sorting capabilities
  - Global search across all columns
  - Individual column search filters
  - Sortable columns
  - Adjustable number of records per page
- Download the converted CSV file
- Handles both flat and nested JSON structures

## Installation

1. Clone this repository
2. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

### Option 1: Direct Command

```bash
cd json2csv
source .venv/bin/activate
uvicorn app.main:app --reload
```

The application will be available at http://127.0.0.1:8000

### Option 2: Convenience Script

Use the provided shell script:

```bash
chmod +x start_converter.sh
./start_converter.sh
```

### Option 3: Background Service (Recommended)

The application can run as a background service with convenient management commands:

```bash
chmod +x start_converter.sh
./start_converter.sh start      # Start the service in the background
./start_converter.sh stop       # Stop the service
./start_converter.sh restart    # Restart the service
./start_converter.sh status     # Check service status
./start_converter.sh logs       # View the last 50 lines of logs
./start_converter.sh follow     # Follow the log output in real-time
```

### Option 4: Terminal Alias

Set up a convenient terminal alias to manage the service from anywhere:

```bash
chmod +x setup_alias.sh
./setup_alias.sh
```

This will add a `json2csv` alias to your shell configuration file (.zshrc or .bashrc).
After setting up, you can manage the service by typing:

```bash
json2csv                # Start the service in the background
json2csv start          # Start the service in the background
json2csv stop           # Stop the running service
json2csv restart        # Restart the service
json2csv status         # Check if the service is running
json2csv logs           # Display the last 50 lines of logs
json2csv follow         # Follow the log output in real-time
```

## Usage

1. Visit the application in your browser
2. Choose to either paste JSON text or upload a JSON file
3. Click "Convert to CSV"
4. View and interact with the data in the table:
   - Use the search box in the upper right to search across all columns
   - Use the search fields under each column header to filter by specific columns
   - Click on column headers to sort
   - Use the "Reset Filters" button to clear all filters
5. Download the CSV file using the "Download CSV" button

## Requirements

- Python 3.7+
- FastAPI
- Pandas
- Uvicorn
- Jinja2 