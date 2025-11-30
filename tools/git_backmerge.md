# Git Branch Back-Merge Workflow

This document outlines an interactive workflow script for safely back-merging changes from the main branch into a feature branch. The script automates context switching, branch updates, and guides the user through conflict resolution and pushing changes.

## Prerequisites

* Git installed and configured
* Working directory is within a Git repository
* The `main` branch exists and is the primary integration branch
* User has necessary permissions to push to remote branches

## Instructions for Use

This workflow is designed to be **semi-automated** with strategic user interaction points. When you need to back-merge main into a feature branch, simply run this script. 

The **script will automatically handle:**
1. **Safely stashing** any uncommitted changes on your current branch
2. **Switching to main** and updating it from remote
3. **Listing all available branches** for easy selection
4. **Switching to your chosen branch** and updating it
5. **Initiating the back-merge** from main
6. **Detecting merge conflicts** and pausing for resolution
7. **Returning to your original branch** after completion

The **user is responsible for:**
1. **Selecting the target branch** from the displayed list
2. **Resolving any merge conflicts** if they occur
3. **Reviewing and confirming** the merge commit
4. **Pushing the merged changes** to remote

## Workflow Steps

### Step 1: Save Current Work State

Before switching branches, we need to preserve any uncommitted changes.

**Command:**
```bash
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if ! git diff-index --quiet HEAD --; then
    echo "Uncommitted changes detected. Stashing..."
    git stash push -m "Auto-stash before back-merge workflow at $(date)"
    STASHED=true
else
    echo "No uncommitted changes detected."
    STASHED=false
fi
```

**Explanation:**
* `git rev-parse --abbrev-ref HEAD`: Captures the current branch name for later return
* `git diff-index --quiet HEAD --`: Checks if there are uncommitted changes (returns non-zero if changes exist)
* `git stash push -m "..."`: Stashes changes with a timestamped message
* `STASHED=true`: Flag to remember if we need to pop the stash later

### Step 2: Update Main Branch

Switch to main and ensure it's synchronized with the remote repository.

**Command:**
```bash
echo "Switching to main branch..."
git checkout main

echo "Updating main from remote..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "Error: Failed to update main branch"
    exit 1
fi

echo "Fetching all remote branches..."
git fetch -a

echo "✓ Main branch updated successfully"
```

**Explanation:**
* `git checkout main`: Switches to the main branch
* `git pull origin main`: Fetches and merges latest changes from remote
* `$?`: Captures exit code of previous command (0 = success)
* `git fetch -a`: Fetches all remote branches and their updates (ensures complete sync with remote)
* Error handling ensures we don't proceed if main can't be updated

### Step 3: Select Target Branch

Display all local branches and prompt user to select one.

**Command:**
```bash
echo ""
echo "========================================="
echo "Available Branches:"
echo "========================================="
git branch | sed 's/^..//g' | nl

echo ""
read -p "Which branch number do you want to back-merge into? " BRANCH_NUMBER

SELECTED_BRANCH=$(git branch | sed 's/^..//g' | sed -n "${BRANCH_NUMBER}p")

if [ -z "$SELECTED_BRANCH" ]; then
    echo "Error: Invalid branch selection"
    exit 1
fi

echo "Selected branch: $SELECTED_BRANCH"
```

**Explanation:**
* `git branch`: Lists all local branches (prefixed with `*` for current branch)
* `sed 's/^..//g'`: Removes the first two characters (the `*` marker and space)
* `nl`: Numbers the lines for easy selection
* `read -p`: Prompts user for input
* `sed -n "${BRANCH_NUMBER}p"`: Extracts the branch name at the selected line number

### Step 4: Checkout and Update Target Branch

Switch to the selected branch and update it from remote.

**Command:**
```bash
echo "Checking out branch: $SELECTED_BRANCH"
git checkout "$SELECTED_BRANCH"

if [ $? -ne 0 ]; then
    echo "Error: Failed to checkout $SELECTED_BRANCH"
    exit 1
fi

echo "Updating $SELECTED_BRANCH from remote..."
git pull origin "$SELECTED_BRANCH"

if [ $? -ne 0 ]; then
    echo "Warning: Could not pull from remote (branch may not exist remotely yet)"
fi

echo "✓ Switched to and updated $SELECTED_BRANCH"
```

**Explanation:**
* `git checkout "$SELECTED_BRANCH"`: Switches to the user-selected branch
* First error check ensures the branch exists and is accessible
* `git pull origin "$SELECTED_BRANCH"`: Updates from remote (may fail for new branches)
* Warning instead of error for pull failure (new branches won't have remote counterpart)

### Step 5: Back-Merge Main into Target Branch

Merge the updated main branch into the current feature branch.

**Command:**
```bash
echo ""
echo "========================================="
echo "Back-merging main into $SELECTED_BRANCH"
echo "========================================="

git merge main

MERGE_EXIT_CODE=$?
```

**Explanation:**
* `git merge main`: Merges main branch into current branch
* Captures exit code to detect conflicts (non-zero = conflicts or errors)

### Step 6: Handle Merge Conflicts (User Interaction)

If conflicts occur, guide the user through resolution.

**Command:**
```bash
if [ $MERGE_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "⚠️  MERGE CONFLICTS DETECTED ⚠️"
    echo "========================================="
    echo "Conflicted files:"
    git status --short | grep '^UU\|^AA\|^DD\|^AU\|^UA\|^DU\|^UD'
    echo ""
    echo "Please resolve the conflicts manually:"
    echo "1. Edit the conflicted files"
    echo "2. Mark them as resolved: git add <file>"
    echo "3. Press ENTER when ready to continue..."
    echo "========================================="
    
    read -p "Press ENTER after resolving conflicts..."
    
    # Verify conflicts are resolved
    if git diff --name-only --diff-filter=U | grep -q .; then
        echo "Error: Unresolved conflicts still exist"
        echo "Aborting workflow. Run 'git merge --abort' to cancel the merge."
        exit 1
    fi
    
    echo "✓ Conflicts resolved"
else
    echo "✓ Merge completed without conflicts"
fi
```

**Explanation:**
* `git status --short | grep '^UU...'`: Shows only files with merge conflicts
* Conflict markers: `UU` = both modified, `AA` = both added, etc.
* `read -p`: Pauses script until user presses ENTER
* `git diff --name-only --diff-filter=U`: Lists unresolved conflicts
* Verification ensures user actually resolved conflicts before proceeding

### Step 7: Commit and Push (User Interaction)

Guide user to finalize the merge and push to remote.

**Command:**
```bash
echo ""
echo "========================================="
echo "Finalizing Merge"
echo "========================================="

# Check if merge is in progress (conflicts were resolved)
if git rev-parse -q --verify MERGE_HEAD > /dev/null; then
    echo "Completing merge commit..."
    read -p "Enter commit message (or press ENTER for default): " COMMIT_MSG
    
    if [ -z "$COMMIT_MSG" ]; then
        git commit --no-edit
    else
        git commit -m "$COMMIT_MSG"
    fi
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to commit merge"
        exit 1
    fi
fi

echo "✓ Merge committed successfully"
echo ""
echo "Branch $SELECTED_BRANCH is now ready to push."
read -p "Do you want to push to remote now? (y/n): " PUSH_CHOICE

if [[ "$PUSH_CHOICE" =~ ^[Yy]$ ]]; then
    echo "Pushing $SELECTED_BRANCH to remote..."
    git push origin "$SELECTED_BRANCH"
    
    if [ $? -eq 0 ]; then
        echo "✓ Successfully pushed to remote"
    else
        echo "Error: Failed to push to remote"
        exit 1
    fi
else
    echo "Skipped push. You can push later with: git push origin $SELECTED_BRANCH"
fi
```

**Explanation:**
* `git rev-parse -q --verify MERGE_HEAD`: Checks if merge is in progress (conflict resolution scenario)
* `git commit --no-edit`: Uses default merge commit message
* User can provide custom message if desired
* Optional push with user confirmation
* `[Yy]` regex matches both 'y' and 'Y'

### Step 8: Return to Original Branch

Switch back to the branch where the workflow started.

**Command:**
```bash
echo ""
echo "========================================="
echo "Returning to original branch..."
echo "========================================="

git checkout "$ORIGINAL_BRANCH"

if [ $? -ne 0 ]; then
    echo "Warning: Could not return to original branch $ORIGINAL_BRANCH"
else
    echo "✓ Returned to $ORIGINAL_BRANCH"
fi

# Restore stashed changes if any
if [ "$STASHED" = true ]; then
    echo "Restoring stashed changes..."
    git stash pop
    
    if [ $? -eq 0 ]; then
        echo "✓ Stashed changes restored"
    else
        echo "Warning: Could not restore stash automatically. Check 'git stash list'"
    fi
fi
```

**Explanation:**
* `git checkout "$ORIGINAL_BRANCH"`: Returns to starting branch
* `git stash pop`: Restores the stashed changes from Step 1
* Graceful error handling with warnings (user can manually fix if needed)

## Full Script Example

```bash
#!/bin/bash

# Exit on error for critical commands, but handle specific errors gracefully
set -euo pipefail

echo "========================================="
echo "Git Branch Back-Merge Workflow"
echo "========================================="

# --- Step 1: Save Current Work State ---
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $ORIGINAL_BRANCH"

if ! git diff-index --quiet HEAD --; then
    echo "Uncommitted changes detected. Stashing..."
    git stash push -m "Auto-stash before back-merge workflow at $(date)"
    STASHED=true
else
    echo "No uncommitted changes detected."
    STASHED=false
fi

# --- Step 2: Update Main Branch ---
echo ""
echo "Switching to main branch..."
git checkout main

echo "Updating main from remote..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "Error: Failed to update main branch"
    exit 1
fi

echo "Fetching all remote branches..."
git fetch -a

echo "✓ Main branch updated successfully"

# --- Step 3: Select Target Branch ---
echo ""
echo "========================================="
echo "Available Branches:"
echo "========================================="
git branch | sed 's/^..//g' | nl

echo ""
read -p "Which branch number do you want to back-merge into? " BRANCH_NUMBER

SELECTED_BRANCH=$(git branch | sed 's/^..//g' | sed -n "${BRANCH_NUMBER}p")

if [ -z "$SELECTED_BRANCH" ]; then
    echo "Error: Invalid branch selection"
    # Return to original branch before exiting
    git checkout "$ORIGINAL_BRANCH"
    exit 1
fi

echo "Selected branch: $SELECTED_BRANCH"

# --- Step 4: Checkout and Update Target Branch ---
echo "Checking out branch: $SELECTED_BRANCH"
git checkout "$SELECTED_BRANCH"

if [ $? -ne 0 ]; then
    echo "Error: Failed to checkout $SELECTED_BRANCH"
    git checkout "$ORIGINAL_BRANCH"
    exit 1
fi

echo "Updating $SELECTED_BRANCH from remote..."
set +e  # Temporarily allow errors
git pull origin "$SELECTED_BRANCH"
PULL_EXIT=$?
set -e  # Re-enable exit on error

if [ $PULL_EXIT -ne 0 ]; then
    echo "Warning: Could not pull from remote (branch may not exist remotely yet)"
fi

echo "✓ Switched to and updated $SELECTED_BRANCH"

# --- Step 5: Back-Merge Main ---
echo ""
echo "========================================="
echo "Back-merging main into $SELECTED_BRANCH"
echo "========================================="

set +e  # Allow merge to fail (conflicts expected)
git merge main
MERGE_EXIT_CODE=$?
set -e

# --- Step 6: Handle Merge Conflicts ---
if [ $MERGE_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "⚠️  MERGE CONFLICTS DETECTED ⚠️"
    echo "========================================="
    echo "Conflicted files:"
    git status --short | grep '^UU\|^AA\|^DD\|^AU\|^UA\|^DU\|^UD'
    echo ""
    echo "Please resolve the conflicts manually:"
    echo "1. Edit the conflicted files"
    echo "2. Mark them as resolved: git add <file>"
    echo "3. Press ENTER when ready to continue..."
    echo "========================================="
    
    read -p "Press ENTER after resolving conflicts..."
    
    # Verify conflicts are resolved
    if git diff --name-only --diff-filter=U | grep -q .; then
        echo "Error: Unresolved conflicts still exist"
        echo "Aborting workflow. Run 'git merge --abort' to cancel the merge."
        exit 1
    fi
    
    echo "✓ Conflicts resolved"
else
    echo "✓ Merge completed without conflicts"
fi

# --- Step 7: Commit and Push ---
echo ""
echo "========================================="
echo "Finalizing Merge"
echo "========================================="

# Check if merge is in progress (conflicts were resolved)
if git rev-parse -q --verify MERGE_HEAD > /dev/null 2>&1; then
    echo "Completing merge commit..."
    read -p "Enter commit message (or press ENTER for default): " COMMIT_MSG
    
    if [ -z "$COMMIT_MSG" ]; then
        git commit --no-edit
    else
        git commit -m "$COMMIT_MSG"
    fi
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to commit merge"
        exit 1
    fi
fi

echo "✓ Merge committed successfully"
echo ""
echo "Branch $SELECTED_BRANCH is now ready to push."
read -p "Do you want to push to remote now? (y/n): " PUSH_CHOICE

if [[ "$PUSH_CHOICE" =~ ^[Yy]$ ]]; then
    echo "Pushing $SELECTED_BRANCH to remote..."
    git push origin "$SELECTED_BRANCH"
    
    if [ $? -eq 0 ]; then
        echo "✓ Successfully pushed to remote"
    else
        echo "Error: Failed to push to remote"
        exit 1
    fi
else
    echo "Skipped push. You can push later with: git push origin $SELECTED_BRANCH"
fi

# --- Step 8: Return to Original Branch ---
echo ""
echo "========================================="
echo "Returning to original branch..."
echo "========================================="

git checkout "$ORIGINAL_BRANCH"

if [ $? -ne 0 ]; then
    echo "Warning: Could not return to original branch $ORIGINAL_BRANCH"
else
    echo "✓ Returned to $ORIGINAL_BRANCH"
fi

# Restore stashed changes if any
if [ "$STASHED" = true ]; then
    echo "Restoring stashed changes..."
    set +e
    git stash pop
    STASH_POP_EXIT=$?
    set -e
    
    if [ $STASH_POP_EXIT -eq 0 ]; then
        echo "✓ Stashed changes restored"
    else
        echo "Warning: Could not restore stash automatically. Check 'git stash list'"
    fi
fi

echo ""
echo "========================================="
echo "Summary:"
echo "  Original branch: $ORIGINAL_BRANCH"
echo "  Updated branch:  $SELECTED_BRANCH"
echo "  Merge status:    Complete"
echo "========================================="
```

## Usage Example

```bash
# Make the script executable
chmod +x git_backmerge.sh

# Run the workflow
./git_backmerge.sh
```

**Example Output:**
```
=========================================
Git Branch Back-Merge Workflow
=========================================
Current branch: feature/new-api
No uncommitted changes detected.

Switching to main branch...
Updating main from remote...
Fetching all remote branches...
✓ Main branch updated successfully

=========================================
Available Branches:
=========================================
     1  feature/new-api
     2  feature/redesign
     3  bugfix/login-issue
     4  main

Which branch number do you want to back-merge into? 2
Selected branch: feature/redesign
Checking out branch: feature/redesign
✓ Switched to and updated feature/redesign

=========================================
Back-merging main into feature/redesign
=========================================
✓ Merge completed without conflicts
✓ Merge committed successfully

Branch feature/redesign is now ready to push.
Do you want to push to remote now? (y/n): y
Pushing feature/redesign to remote...
✓ Successfully pushed to remote

=========================================
Returning to original branch...
=========================================
✓ Returned to feature/new-api

=========================================
Summary:
  Original branch: feature/new-api
  Updated branch:  feature/redesign
  Merge status:    Complete
=========================================
```

## Error Handling

The script includes comprehensive error handling:

- **Main update fails**: Script exits with error message
- **Invalid branch selection**: Script returns to original branch and exits
- **Checkout fails**: Script returns to original branch and exits
- **Unresolved conflicts**: Script exits with instructions to manually abort
- **Commit fails**: Script exits with error message
- **Push fails**: Script reports error but doesn't exit (user can retry manually)
- **Return to original branch fails**: Warning displayed (user can manually switch)
- **Stash pop fails**: Warning displayed (user can manually apply stash)

## Notes

- The script uses `set -euo pipefail` for robust error handling but selectively disables it (`set +e`) for commands where failures are expected (merge conflicts, optional pull)
- Branch names with spaces are properly handled using quoted variables
- The script preserves your working state by stashing/popping changes
- You can safely abort at any user prompt with `Ctrl+C`
- If you abort during conflict resolution, run `git merge --abort` to clean up
