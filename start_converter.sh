#!/bin/bash

# Path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${PROJECT_DIR}/.json2csv.pid"
LOG_FILE="${PROJECT_DIR}/json2csv.log"

# Function to start the service
start_service() {
    if [ -f "${PID_FILE}" ] && ps -p $(cat "${PID_FILE}") > /dev/null 2>&1; then
        echo "JSON to CSV Converter is already running."
        echo "PID: $(cat "${PID_FILE}")"
        return 0
    fi

    # Activate virtual environment
    source "${PROJECT_DIR}/.venv/bin/activate"

    # Start the service in the background
    cd "${PROJECT_DIR}"
    nohup uvicorn app.main:app --host 127.0.0.1 --port 3033 > "${LOG_FILE}" 2>&1 &
    
    # Save the PID
    echo $! > "${PID_FILE}"
    
    echo "JSON to CSV Converter started in the background."
    echo "Access the application at http://127.0.0.1:3033"
    echo "PID: $(cat "${PID_FILE}")"
    echo "Logs: ${LOG_FILE}"
}

# Function to stop the service
stop_service() {
    if [ -f "${PID_FILE}" ]; then
        PID=$(cat "${PID_FILE}")
        if ps -p ${PID} > /dev/null 2>&1; then
            echo "Stopping JSON to CSV Converter (PID: ${PID})..."
            kill ${PID}
            sleep 2
            if ps -p ${PID} > /dev/null 2>&1; then
                echo "Service didn't stop gracefully. Forcing..."
                kill -9 ${PID}
            fi
            echo "Service stopped."
        else
            echo "JSON to CSV Converter is not running."
        fi
        rm -f "${PID_FILE}"
    else
        echo "JSON to CSV Converter is not running."
    fi
}

# Function to check status
status_service() {
    if [ -f "${PID_FILE}" ] && ps -p $(cat "${PID_FILE}") > /dev/null 2>&1; then
        echo "JSON to CSV Converter is running."
        echo "PID: $(cat "${PID_FILE}")"
        echo "Access the application at http://127.0.0.1:3033"
    else
        echo "JSON to CSV Converter is not running."
        # Clean up stale PID file if it exists
        [ -f "${PID_FILE}" ] && rm -f "${PID_FILE}"
    fi
}

# Function to display logs
show_logs() {
    if [ -f "${LOG_FILE}" ]; then
        tail -n 50 "${LOG_FILE}"
    else
        echo "Log file does not exist."
    fi
}

# Function to follow logs
follow_logs() {
    if [ -f "${LOG_FILE}" ]; then
        tail -f "${LOG_FILE}"
    else
        echo "Log file does not exist."
    fi
}

# Parse command line arguments
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        sleep 2
        start_service
        ;;
    status)
        status_service
        ;;
    logs)
        show_logs
        ;;
    follow)
        follow_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|follow}"
        echo "  start   - Start the JSON to CSV Converter in the background"
        echo "  stop    - Stop the running service"
        echo "  restart - Restart the service"
        echo "  status  - Check if the service is running"
        echo "  logs    - Display the last 50 lines of logs"
        echo "  follow  - Follow the log output in real-time"
        
        # For backward compatibility, if no argument is provided, start the service
        if [ -z "$1" ]; then
            start_service
        else
            exit 1
        fi
        ;;
esac

exit 0 