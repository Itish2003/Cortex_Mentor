# GitHub Issue to Branch Workflow

This document outlines an automated workflow for transitioning from a GitHub issue URL to working on its linked branch. The script fetches the latest remote data, stashes uncommitted work, checks out the issue's branch, and displays the issue details to help you start working immediately.

## Prerequisites

* GitHub CLI (`gh`) installed and authenticated
* Git installed and configured
* Working directory is within a Git repository
* The repository is connected to a GitHub remote
* User has permissions to access the issue and branch

## Instructions for Use

This workflow is designed to **quickly transition you from issue to code**. When you want to start working on a GitHub issue, simply provide the issue URL and let the script handle the rest.

The **script will automatically handle:**
1. **Fetching all remote branches** to ensure you have the latest branch information
2. **Checking for uncommitted changes** and stashing them safely
3. **Extracting the issue number** from the provided URL
4. **Finding and checking out** the branch linked to the issue
5. **Displaying the issue details** (title, body, labels, assignees) for context
6. **Providing a summary** of what branch you're on and what to work on

The **user is responsible for:**
1. **Providing a valid GitHub issue URL**
2. **Starting development** based on the displayed issue details

## Workflow Steps

### Step 1: Accept Issue URL Input

The script accepts a GitHub issue URL as the primary input.

**Command:**
```bash
ISSUE_URL="$1"

if [ -z "$ISSUE_URL" ]; then
    echo "Error: Please provide a GitHub issue URL"
    echo "Usage: $0 <issue-url>"
    exit 1
fi

echo "========================================="
echo "GitHub Issue to Branch Workflow"
echo "========================================="
echo "Issue URL: $ISSUE_URL"
```

**Explanation:**
* `$1`: First command-line argument (the issue URL)
* `[ -z "$ISSUE_URL" ]`: Checks if the variable is empty
* Usage instructions displayed if no URL provided

### Step 2: Fetch All Remote Branches

Ensure we have the latest information about all remote branches.

**Command:**
```bash
echo ""
echo "Fetching all remote branches..."
git fetch -a

if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch remote branches"
    exit 1
fi

echo "✓ Remote branches fetched successfully"
```

**Explanation:**
* `git fetch -a`: Fetches all remotes and their branches
* Ensures we have up-to-date branch information before checking out
* Exit code check ensures fetch succeeded

### Step 3: Check Git Status and Stash Changes

Preserve any uncommitted work before switching branches.

**Command:**
```bash
echo ""
echo "Checking for uncommitted changes..."

if ! git diff-index --quiet HEAD --; then
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    STASH_MESSAGE="Auto-stash before issue workflow at $TIMESTAMP"
    
    echo "Uncommitted changes detected. Stashing with message:"
    echo "  '$STASH_MESSAGE'"
    
    git stash push -m "$STASH_MESSAGE"
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to stash changes"
        exit 1
    fi
    
    echo "✓ Changes stashed successfully"
    echo "  (You can restore later with: git stash pop)"
else
    echo "✓ No uncommitted changes detected"
fi
```

**Explanation:**
* `git diff-index --quiet HEAD --`: Checks for uncommitted changes (both staged and unstaged)
* `date +"%Y-%m-%d_%H-%M-%S"`: Creates a timestamp for unique stash identification
* `git stash push -m`: Stashes with a descriptive message including timestamp
* Provides clear instructions for how to restore stashed changes later

### Step 4: Extract Issue Number from URL

Parse the issue number from the GitHub URL.

**Command:**
```bash
echo ""
echo "Extracting issue number from URL..."

# GitHub issue URLs are in format: https://github.com/owner/repo/issues/123
ISSUE_NUMBER=$(echo "$ISSUE_URL" | grep -oE '[0-9]+$')

if [ -z "$ISSUE_NUMBER" ]; then
    echo "Error: Could not extract issue number from URL: $ISSUE_URL"
    echo "Expected format: https://github.com/owner/repo/issues/NUMBER"
    exit 1
fi

echo "✓ Extracted issue number: #$ISSUE_NUMBER"
```

**Explanation:**
* `grep -oE '[0-9]+$'`: Extracts only the trailing digits from the URL
* `-o`: Only output the matched part
* `-E`: Extended regex
* `[0-9]+$`: One or more digits at the end of the string
* Validates that extraction succeeded before proceeding

### Step 5: Get Branch Linked to Issue

Use GitHub CLI to find the branch associated with this issue.

**Command:**
```bash
echo ""
echo "Finding branch linked to issue #$ISSUE_NUMBER..."

# Use gh issue develop --list to see linked branches
BRANCH_INFO=$(gh issue develop $ISSUE_NUMBER --list 2>&1)

if echo "$BRANCH_INFO" | grep -q "no development branch"; then
    echo "⚠️  No branch is currently linked to issue #$ISSUE_NUMBER"
    echo ""
    read -p "Would you like to create and link a new branch? (y/n): " CREATE_CHOICE
    
    if [[ "$CREATE_CHOICE" =~ ^[Yy]$ ]]; then
        echo "Creating and linking a new branch for issue #$ISSUE_NUMBER..."
        gh issue develop $ISSUE_NUMBER --checkout
        LINKED_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    else
        echo "Workflow cancelled. No branch to checkout."
        exit 0
    fi
else
    # Extract the branch name from the output
    LINKED_BRANCH=$(echo "$BRANCH_INFO" | grep -oE '[a-zA-Z0-9/_-]+' | head -1)
    
    if [ -z "$LINKED_BRANCH" ]; then
        echo "Error: Could not determine linked branch name"
        exit 1
    fi
    
    echo "✓ Found linked branch: $LINKED_BRANCH"
fi
```

**Explanation:**
* `gh issue develop $ISSUE_NUMBER --list`: Lists branches linked to the issue
* `2>&1`: Captures both stdout and stderr
* `grep -q "no development branch"`: Checks if no branch is linked
* Offers to create a new branch if none exists
* `gh issue develop $ISSUE_NUMBER --checkout`: Creates, links, and checks out a new branch
* `grep -oE '[a-zA-Z0-9/_-]+'`: Extracts branch name from output

### Step 6: Checkout the Linked Branch

Switch to the branch associated with the issue.

**Command:**
```bash
echo ""
echo "Checking out branch: $LINKED_BRANCH..."

# Only checkout if we're not already on it (could be the case if we just created it)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "$LINKED_BRANCH" ]; then
    echo "✓ Already on branch $LINKED_BRANCH"
else
    git checkout "$LINKED_BRANCH"
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to checkout branch $LINKED_BRANCH"
        exit 1
    fi
    
    echo "✓ Switched to branch $LINKED_BRANCH"
fi

# Pull latest changes from remote if branch exists on remote
echo "Updating branch from remote..."
set +e  # Temporarily allow errors
git pull origin "$LINKED_BRANCH" 2>/dev/null
PULL_EXIT=$?
set -e

if [ $PULL_EXIT -eq 0 ]; then
    echo "✓ Branch updated from remote"
else
    echo "ℹ️  Branch does not exist on remote (new branch)"
fi
```

**Explanation:**
* `git rev-parse --abbrev-ref HEAD`: Gets current branch name
* Checks if already on target branch (avoids unnecessary checkout)
* `git checkout "$LINKED_BRANCH"`: Switches to the linked branch
* `set +e`: Temporarily disables exit-on-error for optional pull
* `git pull origin "$LINKED_BRANCH" 2>/dev/null`: Attempts to update from remote (may fail for new branches)
* Different messages for existing vs. new branches

### Step 7: Display Issue Details

Show the issue information to provide context for development.

**Command:**
```bash
echo ""
echo "========================================="
echo "Issue Details"
echo "========================================="

# Fetch issue details as JSON
ISSUE_JSON=$(gh issue view $ISSUE_NUMBER --json title,body,labels,assignees,state,url)

# Extract and display key fields
ISSUE_TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
ISSUE_BODY=$(echo "$ISSUE_JSON" | jq -r '.body')
ISSUE_STATE=$(echo "$ISSUE_JSON" | jq -r '.state')
ISSUE_LABELS=$(echo "$ISSUE_JSON" | jq -r '.labels[].name' | tr '\n' ', ' | sed 's/, $//')
ISSUE_ASSIGNEES=$(echo "$ISSUE_JSON" | jq -r '.assignees[].login' | tr '\n' ', ' | sed 's/, $//')

echo "Title:     $ISSUE_TITLE"
echo "State:     $ISSUE_STATE"
echo "Labels:    ${ISSUE_LABELS:-None}"
echo "Assignees: ${ISSUE_ASSIGNEES:-None}"
echo ""
echo "Description:"
echo "----------------------------------------"
echo "$ISSUE_BODY"
echo "========================================="
```

**Explanation:**
* `gh issue view $ISSUE_NUMBER --json ...`: Fetches issue data in JSON format
* `jq -r '.title'`: Extracts the title field from JSON
* `jq -r '.labels[].name'`: Extracts all label names as separate lines
* `tr '\n' ', '`: Converts newlines to comma-separated list
* `sed 's/, $//'`: Removes trailing comma and space
* `${ISSUE_ASSIGNEES:-None}`: Displays "None" if variable is empty

### Step 8: Provide Workflow Summary

Display a summary of the workflow completion and next steps.

**Command:**
```bash
echo ""
echo "========================================="
echo "Workflow Complete!"
echo "========================================="
echo "✓ Branch:       $LINKED_BRANCH"
echo "✓ Issue:        #$ISSUE_NUMBER - $ISSUE_TITLE"
echo "✓ Issue URL:    $ISSUE_URL"
echo ""
echo "You're now ready to start working on this issue."
echo "When done, remember to:"
echo "  1. Commit your changes"
echo "  2. Push to remote: git push origin $LINKED_BRANCH"
echo "  3. Create a pull request if needed"
echo "========================================="
```

**Explanation:**
* Summarizes what was accomplished
* Shows current branch and issue information
* Provides next-step reminders for the development workflow
* Clear visual separation with borders

## Full Script Example

```bash
#!/bin/bash

# Exit on error for critical commands, but handle specific errors gracefully
set -euo pipefail

# --- Step 1: Accept Issue URL Input ---
ISSUE_URL="$1"

if [ -z "$ISSUE_URL" ]; then
    echo "Error: Please provide a GitHub issue URL"
    echo "Usage: $0 <issue-url>"
    exit 1
fi

echo "========================================="
echo "GitHub Issue to Branch Workflow"
echo "========================================="
echo "Issue URL: $ISSUE_URL"

# --- Step 2: Fetch All Remote Branches ---
echo ""
echo "Fetching all remote branches..."
git fetch -a

if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch remote branches"
    exit 1
fi

echo "✓ Remote branches fetched successfully"

# --- Step 3: Check Git Status and Stash Changes ---
echo ""
echo "Checking for uncommitted changes..."

if ! git diff-index --quiet HEAD --; then
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    STASH_MESSAGE="Auto-stash before issue workflow at $TIMESTAMP"
    
    echo "Uncommitted changes detected. Stashing with message:"
    echo "  '$STASH_MESSAGE'"
    
    git stash push -m "$STASH_MESSAGE"
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to stash changes"
        exit 1
    fi
    
    echo "✓ Changes stashed successfully"
    echo "  (You can restore later with: git stash pop)"
else
    echo "✓ No uncommitted changes detected"
fi

# --- Step 4: Extract Issue Number from URL ---
echo ""
echo "Extracting issue number from URL..."

# GitHub issue URLs are in format: https://github.com/owner/repo/issues/123
ISSUE_NUMBER=$(echo "$ISSUE_URL" | grep -oE '[0-9]+$')

if [ -z "$ISSUE_NUMBER" ]; then
    echo "Error: Could not extract issue number from URL: $ISSUE_URL"
    echo "Expected format: https://github.com/owner/repo/issues/NUMBER"
    exit 1
fi

echo "✓ Extracted issue number: #$ISSUE_NUMBER"

# --- Step 5: Get Branch Linked to Issue ---
echo ""
echo "Finding branch linked to issue #$ISSUE_NUMBER..."

# Use gh issue develop --list to see linked branches
set +e  # Temporarily allow errors
BRANCH_INFO=$(gh issue develop $ISSUE_NUMBER --list 2>&1)
DEVELOP_EXIT=$?
set -e

if [ $DEVELOP_EXIT -ne 0 ] || echo "$BRANCH_INFO" | grep -q "no development branch"; then
    echo "⚠️  No branch is currently linked to issue #$ISSUE_NUMBER"
    echo ""
    read -p "Would you like to create and link a new branch? (y/n): " CREATE_CHOICE
    
    if [[ "$CREATE_CHOICE" =~ ^[Yy]$ ]]; then
        echo "Creating and linking a new branch for issue #$ISSUE_NUMBER..."
        gh issue develop $ISSUE_NUMBER --checkout
        LINKED_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        echo "✓ Created and switched to branch: $LINKED_BRANCH"
    else
        echo "Workflow cancelled. No branch to checkout."
        exit 0
    fi
else
    # Extract the branch name from the output
    LINKED_BRANCH=$(echo "$BRANCH_INFO" | grep -oE '[a-zA-Z0-9/_-]+' | head -1)
    
    if [ -z "$LINKED_BRANCH" ]; then
        echo "Error: Could not determine linked branch name"
        exit 1
    fi
    
    echo "✓ Found linked branch: $LINKED_BRANCH"
fi

# --- Step 6: Checkout the Linked Branch ---
echo ""
echo "Checking out branch: $LINKED_BRANCH..."

# Only checkout if we're not already on it (could be the case if we just created it)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "$LINKED_BRANCH" ]; then
    echo "✓ Already on branch $LINKED_BRANCH"
else
    git checkout "$LINKED_BRANCH"
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to checkout branch $LINKED_BRANCH"
        exit 1
    fi
    
    echo "✓ Switched to branch $LINKED_BRANCH"
fi

# Pull latest changes from remote if branch exists on remote
echo "Updating branch from remote..."
set +e  # Temporarily allow errors
git pull origin "$LINKED_BRANCH" 2>/dev/null
PULL_EXIT=$?
set -e

if [ $PULL_EXIT -eq 0 ]; then
    echo "✓ Branch updated from remote"
else
    echo "ℹ️  Branch does not exist on remote (new branch)"
fi

# --- Step 7: Display Issue Details ---
echo ""
echo "========================================="
echo "Issue Details"
echo "========================================="

# Fetch issue details as JSON
ISSUE_JSON=$(gh issue view $ISSUE_NUMBER --json title,body,labels,assignees,state,url)

# Extract and display key fields
ISSUE_TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
ISSUE_BODY=$(echo "$ISSUE_JSON" | jq -r '.body')
ISSUE_STATE=$(echo "$ISSUE_JSON" | jq -r '.state')
ISSUE_LABELS=$(echo "$ISSUE_JSON" | jq -r '.labels[].name' | tr '\n' ', ' | sed 's/, $//')
ISSUE_ASSIGNEES=$(echo "$ISSUE_JSON" | jq -r '.assignees[].login' | tr '\n' ', ' | sed 's/, $//')

echo "Title:     $ISSUE_TITLE"
echo "State:     $ISSUE_STATE"
echo "Labels:    ${ISSUE_LABELS:-None}"
echo "Assignees: ${ISSUE_ASSIGNEES:-None}"
echo ""
echo "Description:"
echo "----------------------------------------"
echo "$ISSUE_BODY"
echo "========================================="

# --- Step 8: Provide Workflow Summary ---
echo ""
echo "========================================="
echo "Workflow Complete!"
echo "========================================="
echo "✓ Branch:       $LINKED_BRANCH"
echo "✓ Issue:        #$ISSUE_NUMBER - $ISSUE_TITLE"
echo "✓ Issue URL:    $ISSUE_URL"
echo ""
echo "You're now ready to start working on this issue."
echo "When done, remember to:"
echo "  1. Commit your changes"
echo "  2. Push to remote: git push origin $LINKED_BRANCH"
echo "  3. Create a pull request if needed"
echo "========================================="
```

## Usage Example

```bash
# Make the script executable
chmod +x issue_to_branch.sh

# Run the workflow with an issue URL
./issue_to_branch.sh https://github.com/owner/repo/issues/42
```

**Example Output:**
```
=========================================
GitHub Issue to Branch Workflow
=========================================
Issue URL: https://github.com/owner/repo/issues/42

Fetching all remote branches...
✓ Remote branches fetched successfully

Checking for uncommitted changes...
Uncommitted changes detected. Stashing with message:
  'Auto-stash before issue workflow at 2025-01-15_14-30-22'
✓ Changes stashed successfully
  (You can restore later with: git stash pop)

Extracting issue number from URL...
✓ Extracted issue number: #42

Finding branch linked to issue #42...
✓ Found linked branch: feature/implement-dark-mode

Checking out branch: feature/implement-dark-mode...
✓ Switched to branch feature/implement-dark-mode
Updating branch from remote...
✓ Branch updated from remote

=========================================
Issue Details
=========================================
Title:     Implement dark mode toggle
State:     OPEN
Labels:    enhancement, UI/UX
Assignees: johndoe

Description:
----------------------------------------
Add a dark mode toggle to the application settings.
Users should be able to switch between light and dark themes.
The preference should persist across sessions.
=========================================

=========================================
Workflow Complete!
=========================================
✓ Branch:       feature/implement-dark-mode
✓ Issue:        #42 - Implement dark mode toggle
✓ Issue URL:    https://github.com/owner/repo/issues/42

You're now ready to start working on this issue.
When done, remember to:
  1. Commit your changes
  2. Push to remote: git push origin feature/implement-dark-mode
  3. Create a pull request if needed
=========================================
```

## Error Handling

The script includes comprehensive error handling:

- **No issue URL provided**: Script exits with usage instructions
- **Git fetch fails**: Script exits with error message
- **Stash fails**: Script exits with error message
- **Invalid issue URL format**: Script exits with format example
- **No linked branch found**: Script offers to create and link a new branch
- **Branch creation declined**: Script exits gracefully
- **Checkout fails**: Script exits with error message
- **Pull fails**: Displays info message (normal for new branches)

## Notes

- The script requires `jq` to be installed for JSON parsing
- If no branch is linked to the issue, the script offers to create one using `gh issue develop --checkout`
- Stashed changes are timestamped for easy identification
- The script preserves your working state before switching branches
- You can abort at the "create branch" prompt with `n` or `Ctrl+C`
- Branch updates from remote are optional (won't fail for new branches)

## Dependencies

- `gh` (GitHub CLI) - for issue and branch management
- `git` - for version control operations
- `jq` - for JSON parsing
- `grep`, `sed`, `tr` - standard Unix text processing tools
