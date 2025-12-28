#!/bin/bash

# Check the current git status
echo "📦 Checking git status..."
git status

# Save current changes to stash if any
if [[ -n $(git status --porcelain) ]]; then
    echo "💾 Stashing local changes..."
    git stash
    
    # Always use rebase to avoid merge commits and handle divergent branches
    echo "🔄 Pulling latest changes with rebase..."
    git pull --rebase origin master
    
    # Apply stashed changes back
    echo "📤 Applying local changes back..."
    git stash pop
    
    # Check for conflicts
    if [[ -n $(git diff --name-only --diff-filter=U) ]]; then
        echo "⚠️  Conflicts detected! Please resolve manually."
        echo "Conflicting files:"
        git diff --name-only --diff-filter=U
        exit 1
    fi
    
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
    echo "✨ No changes detected. Pulling latest anyway..."
    git pull --rebase origin master
    echo "✅ Repository is up to date!"
fi