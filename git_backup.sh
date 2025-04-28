#!/bin/bash

# Check the current git status
echo "📦 Checking git status..."
git status

# Check if there are changes to commit
if [[ -n $(git status --porcelain) ]]; then
    # Add all changes
    echo "➕ Adding all changes..."
    git add .

    # Ask the user for a commit message
    echo "📝 Please enter your commit message:"
    read commit_message

    # Commit the changes with the given message
    echo "💾 Committing your changes..."
    git commit -m "$commit_message"

    # Push the changes to the 'master' branch
    echo "🚀 Pushing changes to 'master' branch..."
    git push -u origin master

    echo "✅ Backup completed successfully!"
else
    echo "✨ No changes detected. Nothing to commit."
fi
