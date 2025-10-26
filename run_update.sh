#!/bin/bash

# Football Performance Comparison - Automated Update Script
# Runs scraper and analysis with logging

# Set environment for cron compatibility
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export SHELL="/bin/bash"

# Set project directory
PROJECT_DIR="/Users/gkb/Desktop/Performance-Comparison"
cd "$PROJECT_DIR" || exit 1

# Create logs directory if it doesn't exist
mkdir -p logs

# Log file with timestamp
LOG_FILE="logs/update_$(date +%Y%m%d_%H%M%S).log"

# Use absolute path to Python in virtual environment
PYTHON_BIN="$PROJECT_DIR/venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$PYTHON_BIN" ]; then
    echo "ERROR: Python virtual environment not found at $PYTHON_BIN" >> "$LOG_FILE"
    exit 1
fi

echo "=====================================================" >> "$LOG_FILE"
echo "Football Performance Comparison - Update Started" >> "$LOG_FILE"
echo "Time: $(date)" >> "$LOG_FILE"
echo "Python: $PYTHON_BIN" >> "$LOG_FILE"
echo "=====================================================" >> "$LOG_FILE"

# Run scraper to fetch latest data
echo -e "\n[1/2] Running scraper..." >> "$LOG_FILE"
"$PYTHON_BIN" scraper.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Scraper completed successfully" >> "$LOG_FILE"
else
    echo "✗ Scraper failed" >> "$LOG_FILE"
    exit 1
fi

# Run analysis
echo -e "\n[2/2] Running analysis..." >> "$LOG_FILE"
"$PYTHON_BIN" analysis.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Analysis completed successfully" >> "$LOG_FILE"
else
    echo "✗ Analysis failed" >> "$LOG_FILE"
    exit 1
fi

echo -e "\n=====================================================" >> "$LOG_FILE"
echo "Update Completed Successfully" >> "$LOG_FILE"
echo "Time: $(date)" >> "$LOG_FILE"
echo "=====================================================" >> "$LOG_FILE"

# Keep only last 10 log files
cd logs
ls -t update_*.log | tail -n +11 | xargs rm -f 2>/dev/null

exit 0

