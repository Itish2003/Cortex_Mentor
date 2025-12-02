# Git Deleted Branch Cleanup Workflow

This document outlines an interactive workflow script for safely identifying and cleaning up local Git branches that no longer exist on the remote GitHub repository. The script automates fetching updates and listing branches, then guides the user through confirming the deletion of local branches.

## Prerequisites

*   Git installed and configured.
*   GitHub CLI (`gh`) installed and authenticated (for potentially identifying remote branches, though `git` commands suffice).
*   Working directory is within a Git repository.
*   User has necessary permissions to fetch from the remote and delete local branches.

## Instructions for Use

This workflow is designed to be **semi-automated** with strategic user interaction points. When you need to clean up local branches, simply run this script.

The **script will automatically handle:**
1.  **Fetching all remote branches** to synchronize local knowledge of the remote.
2.  **Listing all local branches** and all remote-tracking branches.
3.  **Identifying local branches** that no longer have a corresponding remote-tracking branch (meaning they've been deleted from the remote).

The **user is responsible for:**
1.  **Confirming the deletion** of each identified local branch before the `git branch -d` command is executed.

## Workflow Steps

### Step 1: Fetch All Remote Branches

First, we ensure our local repository has the most up-to-date information about remote branches.

**Command:**
```bash
git fetch -a --prune
```

**Explanation:**
*   `git fetch -a`: Fetches all remotes.
*   `--prune`: Removes any remote-tracking references that no longer exist on the remote. This is crucial for accurately identifying deleted branches.

### Step 2: Get Lists of Local and Remote Branches

We need to get distinct lists of local and remote-tracking branches to compare them.

**Command:**
```bash
# Get all local branch names
LOCAL_BRANCHES=$(git branch --format='%(refname:short)')

# Get all remote-tracking branch names (e.g., 'origin/feature-branch')
REMOTE_TRACKING_BRANCHES=$(git branch -r --format='%(refname:short)')

# Extract just the branch names from remote-tracking (e.g., 'feature-branch')
# Assuming 'origin' is the primary remote. Adjust if you have other remotes.
REMOTE_BRANCH_NAMES=$(echo "$REMOTE_TRACKING_BRANCHES" | sed 's/origin\///g' | sort -u)
```

**Explanation:**
*   `git branch --format='%(refname:short)'`: Lists local branches in a short format.
*   `git branch -r --format='%(refname:short)'`: Lists remote-tracking branches in a short format (e.g., `origin/main`).
*   `sed 's/origin\///g'`: Removes the `origin/` prefix to get just the branch name, making it comparable to local branch names.
*   `sort -u`: Sorts and ensures unique entries, useful if there are multiple remotes or duplicates.

### Step 3: Identify Local Branches to Delete

Now, we compare the lists to find local branches that do not have a remote counterpart.

**Command:**
```bash
# Initialize an empty array for branches to delete
BRANCHES_TO_DELETE=()

# Iterate through each local branch
for local_branch in $LOCAL_BRANCHES; do
    # Skip 'main' or other protected branches
    if [[ "$local_branch" == "main" || "$local_branch" == "master" ]]; then
        continue
    fi

    # Check if the local branch exists in the list of remote branch names
    if ! echo "$REMOTE_BRANCH_NAMES" | grep -q "^$local_branch$"; then
        BRANCHES_TO_DELETE+=("$local_branch")
    fi
done

if [ ${#BRANCHES_TO_DELETE[@]} -eq 0 ]; then
    echo "No local branches found that have been deleted from the remote."
    exit 0
fi

echo "Identified local branches that are no longer on the remote:"
for branch in "${BRANCHES_TO_DELETE[@]}"; do
    echo "- $branch"
done
```

**Explanation:**
*   The script iterates through `LOCAL_BRANCHES`.
*   It explicitly skips `main` (and `master`) to prevent accidental deletion of primary branches.
*   `grep -q "^$local_branch$"`: Checks if the `local_branch` exists exactly in the `REMOTE_BRANCH_NAMES` list. The `^` and `$` ensure exact matching.
*   If a local branch has no remote counterpart, it's added to `BRANCHES_TO_DELETE`.

### Step 4: Prompt for User Confirmation and Delete Branches

For each identified branch, the script will ask for user confirmation before executing the delete command.

**Command:**
```bash
echo ""
echo "========================================="
echo "Confirm Deletion of Local Branches"
echo "========================================="

for branch in "${BRANCHES_TO_DELETE[@]}"; do
    read -p "Delete local branch '$branch'? (y/N): " CONFIRM_DELETE
    if [[ "$CONFIRM_DELETE" =~ ^[Yy]$ ]]; then
        echo "Deleting local branch '$branch'..."
        if git branch -d "$branch"; then
            echo "✓ Successfully deleted '$branch'"
        else
            echo "Error: Failed to delete '$branch'. It might have unmerged changes. Use 'git branch -D $branch' to force delete."
        fi
    else
        echo "Skipping deletion of '$branch'."
    fi
done

echo "Cleanup process complete."
```

**Explanation:**
*   The script iterates through the `BRANCHES_TO_DELETE` array.
*   `read -p "Delete local branch '$branch'? (y/N): " CONFIRM_DELETE`: Prompts the user for confirmation.
*   `[[ "$CONFIRM_DELETE" =~ ^[Yy]$ ]]`: Checks if the user input is 'y' or 'Y'.
*   `git branch -d "$branch"`: Deletes the local branch if confirmed.
*   Error handling is included for `git branch -d`, suggesting a force delete (`-D`) if a branch has unmerged changes.

## Full Script Example

```bash
#!/bin/bash

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

echo "========================================="
echo "Git Deleted Branch Cleanup Workflow"
echo "========================================="

# --- Step 1: Fetch All Remote Branches ---
echo "Fetching all remote branches and pruning stale ones..."
git fetch -a --prune
echo "✓ Remote branches updated."

# --- Step 2: Get Lists of Local and Remote Branches ---
echo "Gathering local and remote branch information..."
LOCAL_BRANCHES=$(git branch --format='%(refname:short)')
REMOTE_TRACKING_BRANCHES=$(git branch -r --format='%(refname:short)')
REMOTE_BRANCH_NAMES=$(echo "$REMOTE_TRACKING_BRANCHES" | sed 's/origin\///g' | sort -u)

# --- Step 3: Identify Local Branches to Delete ---
BRANCHES_TO_DELETE=()

for local_branch in $LOCAL_BRANCHES; do
    # Skip 'main' and 'master' to prevent accidental deletion
    if [[ "$local_branch" == "main" || "$local_branch" == "master" ]]; then
        continue
    fi

    # Check if the local branch has a corresponding remote-tracking branch
    if ! echo "$REMOTE_BRANCH_NAMES" | grep -q "^$local_branch$"; then
        BRANCHES_TO_DELETE+=("$local_branch")
    fi
done

if [ ${#BRANCHES_TO_DELETE[@]} -eq 0 ]; then
    echo "No local branches found that have been deleted from the remote."
    echo "Cleanup process complete."
    exit 0
fi

echo "Identified local branches that are no longer on the remote:"
for branch in "${BRANCHES_TO_DELETE[@]}"; do
    echo "- $branch"
done

# --- Step 4: Prompt for User Confirmation and Delete Branches ---
echo ""
echo "========================================="
echo "Confirm Deletion of Local Branches"
echo "========================================="

for branch in "${BRANCHES_TO_DELETE[@]}"; do
    read -p "Delete local branch '$branch'? (y/N): " CONFIRM_DELETE
    if [[ "$CONFIRM_DELETE" =~ ^[Yy]$ ]]; then
        echo "Deleting local branch '$branch'..."
        if git branch -d "$branch"; then
            echo "✓ Successfully deleted '$branch'"
        else
            echo "Error: Failed to delete '$branch'. It might have unmerged changes."
            echo "       You can force delete with: git branch -D '$branch'"
        fi
    else
        echo "Skipping deletion of '$branch'."
    fi
done

echo ""
echo "========================================="
echo "Cleanup process complete."
echo "========================================="
```

## Usage Example

```bash
# Save the script as e.g., 'git_cleanup_deleted_branches.sh'
# Make the script executable
chmod +x git_cleanup_deleted_branches.sh

# Run the workflow
./git_cleanup_deleted_branches.sh
```

**Example Output:**
```
=========================================
Git Deleted Branch Cleanup Workflow
=========================================
Fetching all remote branches and pruning stale ones...
✓ Remote branches updated.
Gathering local and remote branch information...
Identified local branches that are no longer on the remote:
- feature/old-feature-x
- bugfix/bug-y-fixed

=========================================
Confirm Deletion of Local Branches
=========================================
Delete local branch 'feature/old-feature-x'? (y/N): y
Deleting local branch 'feature/old-feature-x'...
✓ Successfully deleted 'feature/old-feature-x'
Delete local branch 'bugfix/bug-y-fixed'? (y/N): n
Skipping deletion of 'bugfix/bug-y-fixed'.

=========================================
Cleanup process complete.
=========================================
```

## Error Handling

*   The script uses `set -euo pipefail` for robust error handling.
*   If `git fetch` or `git branch -d` commands fail, appropriate messages are displayed, and the script might exit or continue with warnings, allowing for manual intervention.
*   The script prompts for confirmation before each deletion, preventing accidental data loss.
*   Suggestions for force deletion (`git branch -D`) are provided if a regular delete fails due to unmerged changes.

## Notes

*   This script assumes `origin` is the primary remote name. If you use other remote names, you may need to adjust the `sed 's/origin\///g'` command to match your remote.
*   Protected branches like `main` and `master` are skipped from deletion. You can extend this list if you have other long-lived branches you wish to protect.
*   You can safely abort at any user prompt with `Ctrl+C`.