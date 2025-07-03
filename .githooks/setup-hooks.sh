#!/bin/bash

set -e

echo "Setting up Git hooks..."

# Get the repository root
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Copy pre-commit hook to .git/hooks/
cp "$REPO_ROOT/.githooks/pre-commit" "$REPO_ROOT/.git/hooks/pre-commit"
chmod +x "$REPO_ROOT/.git/hooks/pre-commit"

echo "Pre-commit hook installed successfully!"
echo "Your commits will now automatically run code quality checks."
