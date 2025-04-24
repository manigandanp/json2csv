#!/bin/bash

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the alias name
ALIAS_NAME="json2csv"

# Check which shell the user is using
if [[ "$SHELL" == *"zsh"* ]]; then
    RC_FILE="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    RC_FILE="$HOME/.bashrc"
    # For macOS, use .bash_profile if it exists
    if [[ "$(uname)" == "Darwin" && -f "$HOME/.bash_profile" ]]; then
        RC_FILE="$HOME/.bash_profile"
    fi
else
    echo "Could not determine your shell. Please manually add the alias to your shell configuration file."
    echo "Add this line: alias $ALIAS_NAME='${PROJECT_DIR}/start_converter.sh'"
    exit 1
fi

# Check if the alias already exists
if grep -q "alias $ALIAS_NAME=" "$RC_FILE"; then
    echo "Alias '$ALIAS_NAME' already exists in $RC_FILE."
    echo "You can manually update it by editing your $RC_FILE file."
else
    # Add the alias to the shell configuration file
    echo "" >> "$RC_FILE"
    echo "# JSON to CSV Converter alias" >> "$RC_FILE"
    echo "alias $ALIAS_NAME='${PROJECT_DIR}/start_converter.sh'" >> "$RC_FILE"
    echo "Alias '$ALIAS_NAME' has been added to $RC_FILE."
    echo "To use it, either restart your terminal or run: source $RC_FILE"
fi

echo ""
echo "Setup complete!"
echo "You can now start the JSON to CSV Converter by typing:"
echo "  $ALIAS_NAME                - Start the service in the background"
echo "  $ALIAS_NAME start          - Start the service in the background"
echo "  $ALIAS_NAME stop           - Stop the running service"
echo "  $ALIAS_NAME restart        - Restart the service"
echo "  $ALIAS_NAME status         - Check if the service is running"
echo "  $ALIAS_NAME logs           - Display the last 50 lines of logs"
echo "  $ALIAS_NAME follow         - Follow the log output in real-time" 