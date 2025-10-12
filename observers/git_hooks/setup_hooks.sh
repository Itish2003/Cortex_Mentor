#!/bin/sh
# This script sets up the Git post-commit hook for the Cortex observer.

# The source Python script for the hook
SOURCE_HOOK="observers/git_hooks/post-commit.py"

# The destination path for the hook within the .git directory
DEST_HOOK=".git/hooks/post-commit"

# Check if the source file exists
if [ ! -f "$SOURCE_HOOK" ]; then
    echo "Error: Source hook script not found at $SOURCE_HOOK"
    exit 1
fi

# Create the .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create a wrapper script at the destination that executes the Python script
# This is more robust than a symlink, especially in different environments.
# It ensures that the python script is run with the correct interpreter.
cat > "$DEST_HOOK" << EOL
#!/bin/sh
# This hook was installed by setup_hooks.sh

# Run the python observer script
python3 "$PWD/$SOURCE_HOOK"
EOL

# Make the hook script executable
chmod +x "$DEST_HOOK"

echo "Successfully installed the Git post-commit hook."
