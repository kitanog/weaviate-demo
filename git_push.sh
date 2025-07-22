#!/bin/bash
# Git Push Helper Script for macOS/Linux
# Usage: ./git_push.sh "Your commit message here"

echo ""
echo "========================================"
echo "       Git Push Helper Script"
echo "========================================"
echo ""

# Check if commit message was provided
if [ -z "$1" ]; then
    echo "ERROR: Please provide a commit message"
    echo "Usage: ./git_push.sh \"Your commit message here\""
    echo ""
    echo "Example: ./git_push.sh \"Fix RAG search and update UI\""
    echo ""
    exit 1
fi

# Store the commit message
COMMIT_MSG="$1"

echo "Current Git Status:"
echo "-------------------"
git status
echo ""

# Ask for confirmation
read -p "Do you want to add all changes and commit with message: '$COMMIT_MSG'? (y/n): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo ""
echo "Adding all changes..."
git add .

echo ""
echo "Committing with message: \"$COMMIT_MSG\""
git commit -m "$COMMIT_MSG"

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Commit failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "Pushing to GitHub..."
git push origin main

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Push failed. Please check the error messages above."
    echo "This might be due to:"
    echo "- No internet connection"
    echo "- Authentication issues"
    echo "- Remote repository issues"
    echo "- Need to pull changes first"
    echo ""
    echo "Try running: git pull origin main"
    exit 1
fi

echo ""
echo "========================================"
echo "      SUCCESS! Changes pushed to GitHub"
echo "========================================"
echo ""