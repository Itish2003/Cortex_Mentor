# Automating GitHub Workflow: Create Issue, Branch, and Pull Request

This document outlines a sequence of `gh` CLI commands to streamline the workflow of creating an issue, subsequently creating a new branch based on that issue, and finally opening a pull request from the new branch back to `main`. The output from each step is designed to feed into the next, ensuring a connected and efficient process.

## Prerequisites

*   GitHub CLI (`gh`) installed and authenticated.
*   Working directory is within a Git repository.
*   The `main` branch exists and is up to date.

## Instructions for Use

This document provides a script to automate the creation of a GitHub issue, a new branch, and a pull request. When interacting with the Gemini agent, you will primarily provide the core request. The **Gemini agent will then take responsibility for:**

1.  **Enhancing Issue Details**: Formulating a comprehensive `ISSUE_TITLE` and `ISSUE_BODY` based on your input, potentially using codebase investigation (`codebase_investigator`) to add factual details or best practices. If clarification is needed, the agent will ask.
2.  **Deciding on Labels**: Listing available labels (`gh label list`) and selecting appropriate ones for the issue.
3.  **Populating Script Variables**: Setting the `ISSUE_TITLE`, `ISSUE_BODY`, and `LABELS` variables within this script before execution.

The script then automates the GitHub workflow based on these prepared parameters.

## Workflow Steps

### Step 1: Create a GitHub Issue

First, we create a new issue. We'll capture its number for subsequent steps.

**Command:**
```bash
ISSUE_TITLE="Brief summary of the issue"
ISSUE_BODY="Detailed description of the problem or feature."

# Create the issue and capture its URL and number
ISSUE_DETAILS=$(gh issue create --title "$ISSUE_TITLE" --body "$ISSUE_BODY" --json url,number)

# Extract the issue number and URL for later use
ISSUE_NUMBER=$(echo "$ISSUE_DETAILS" | jq -r '.number')
ISSUE_URL=$(echo "$ISSUE_DETAILS" | jq -r '.url')

echo "Created issue #$ISSUE_NUMBER: $ISSUE_TITLE"
echo "Issue URL: $ISSUE_URL"
```

**Explanation:**
*   `gh issue create`: Initiates the issue creation process.
*   `--title "$ISSUE_TITLE"`: Sets the title of the issue.
*   `--body "$ISSUE_BODY"`: Sets the body/description of the issue.
*   `--json url,number`: Requests the issue's URL and number in JSON format.
*   `jq -r '.number'` and `jq -r '.url'`: Uses `jq` to parse the JSON output and extract the `number` and `url` fields. This is crucial for linking the subsequent branch and PR to this issue.

### Step 2: Create a New Branch from 'main'

Next, we create a new local branch based on the `main` branch, incorporating the issue number and a slugified version of the issue title for clarity.

**Command:**
```bash
# Assuming ISSUE_NUMBER and ISSUE_TITLE are set from Step 1

# Generate a clean branch name from the issue title (e.g., 'fix-bug-in-feature-123')
# Note: This is a simplified slugification. A more robust solution might be needed for complex titles.
BRANCH_NAME="issue-$ISSUE_NUMBER-$(echo "$ISSUE_TITLE" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-|-$//g')"

git checkout main
git pull origin main
git checkout -b "$BRANCH_NAME"

echo "Created and switched to branch: $BRANCH_NAME"
```

**Explanation:**
*   `BRANCH_NAME="..."`: Constructs a branch name using the issue number and a "slugified" version of the issue title. Slugification replaces spaces and special characters with hyphens and converts to lowercase.
*   `git checkout main`: Switches to the `main` branch.
*   `git pull origin main`: Ensures the `main` branch is up-to-date with the remote.
*   `git checkout -b "$BRANCH_NAME"`: Creates and switches to the new branch.

### Step 3: Create a Pull Request

Finally, we create a pull request from the newly created branch back to `main`, automatically linking it to the issue created in Step 1.

**Command:**
```bash
# Assuming BRANCH_NAME, ISSUE_NUMBER, and ISSUE_URL are set from previous steps

PR_TITLE="Resolves #$ISSUE_NUMBER: $ISSUE_TITLE"
PR_BODY="This pull request addresses issue #$ISSUE_NUMBER.\n\n$ISSUE_URL"

# Push the new branch to remote
git push -u origin "$BRANCH_NAME"

# Create the pull request
PR_DETAILS=$(gh pr create --base main --head "$BRANCH_NAME" --title "$PR_TITLE" --body "$PR_BODY" --json url)

PR_URL=$(echo "$PR_DETAILS" | jq -r '.url')

echo "Created pull request: $PR_TITLE"
echo "Pull Request URL: $PR_URL"
```

**Explanation:**
*   `PR_TITLE="..."`: Constructs a descriptive pull request title, referencing the issue number.
*   `PR_BODY="..."`: Creates a pull request body that links back to the original issue.
*   `git push -u origin "$BRANCH_NAME"`: Pushes the new local branch to the remote repository. The `-u` flag sets the upstream tracking branch.
*   `gh pr create`: Initiates the pull request creation.
*   `--base main`: Specifies `main` as the target branch for the PR.
*   `--head "$BRANCH_NAME"`: Specifies the newly created branch as the source for the PR.
*   `--title "$PR_TITLE"` and `--body "$PR_BODY"`: Sets the title and body of the pull request.
*   `--json url`: Requests the pull request's URL in JSON format.
*   `jq -r '.url'`: Extracts the URL of the created pull request.

## Full Script Example

```bash
#!/bin/bash

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

# --- User Defined Variables ---
# Define your issue title and body here.
# If you are unsure, ask the Gemini agent for assistance.
ISSUE_TITLE="[YOUR_ISSUE_TITLE_HERE]"
ISSUE_BODY="[YOUR_ISSUE_BODY_HERE]"
# Comma-separated labels (e.g., "bug,enhancement,priority: high")
# Note: Labels with spaces (like "priority: high") are supported
LABELS=""

# --- Initial Checks ---
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Error: You are not on the 'main' branch. Please switch to 'main' before running this script."
    exit 1
fi

echo "Updating main branch..."
git pull origin main
echo "Ensured main branch is up to date."

# --- Step 1: Create GitHub Issue ---
echo "Creating GitHub issue..."

# If LABELS is empty, list available labels and prompt for selection (simulated for agent)
if [ -z "$LABELS" ]; then
    echo "Available labels (for Gemini agent to choose from or user to specify):"
    gh label list | awk '{print $1}'
    # In a real interactive scenario, the agent would use this list to ask the user or select
    # For this script, we'll assume LABELS is set by the user or agent before execution.
    echo "Please set the LABELS variable in the script if you want to apply labels."
fi

# Create issue and extract URL and number
ISSUE_URL=$(gh issue create --title "$ISSUE_TITLE" --body "$ISSUE_BODY")
ISSUE_NUMBER=$(echo "$ISSUE_URL" | grep -oE '[0-9]+$')

if [ -z "$ISSUE_NUMBER" ]; then
    echo "Error: Failed to extract issue number from: $ISSUE_URL"
    exit 1
fi

echo "✓ Created issue #$ISSUE_NUMBER: $ISSUE_TITLE"
echo "  URL: $ISSUE_URL"

# --- Step 1.5: Add Labels to the Issue ---
if [ -n "$LABELS" ]; then
    echo "Adding labels to issue #$ISSUE_NUMBER..."
    # Split labels by comma and add each one
    OLD_IFS="$IFS"
    IFS=','
    for label in $LABELS; do
        IFS="$OLD_IFS"
        # Trim whitespace from label
        TRIMMED_LABEL=$(echo "$label" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [ -n "$TRIMMED_LABEL" ]; then
            echo "  Adding label: $TRIMMED_LABEL"
            gh issue edit "$ISSUE_NUMBER" --add-label "$TRIMMED_LABEL"
        fi
    done
    IFS="$OLD_IFS"
    echo "✓ Labels added successfully"
fi

# --- Step 2: Create and Link a New Branch to the Issue ---
echo "Creating and linking new branch using gh issue develop..."

# gh issue develop automatically names the branch well and links it to the issue
# CRITICAL: Must use --checkout flag to actually switch to the new branch
gh issue develop "$ISSUE_NUMBER" --base main --checkout

# Verify we switched branches
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH_NAME" = "main" ]; then
    echo "Error: Failed to switch to new branch (still on main)"
    exit 1
fi

echo "✓ Created and switched to branch: $BRANCH_NAME"

# --- Step 3: Make an Initial Commit (if no changes) ---
echo "Creating initial commit..."
# To ensure a PR can be created, make at least one commit. If there are no actual changes, an empty commit suffices.
if git diff --cached --quiet && git diff --quiet; then
    echo "No changes detected. Creating empty commit to enable PR."
    git commit --allow-empty -m "feat: Initial commit for issue #$ISSUE_NUMBER"
else
    echo "Found changes. Creating commit with changes."
    # Stage all changes if there are unstaged changes
    if ! git diff --quiet; then
        git add -A
    fi
    git commit -m "feat: Work for issue #$ISSUE_NUMBER"
fi
echo "✓ Commit created"

# --- Step 4: Create Pull Request and Link to Issue ---
echo "Pushing branch to remote..."
git push -u origin "$BRANCH_NAME"
echo "✓ Branch pushed"

echo "Creating pull request..."
PR_TITLE="Resolves #$ISSUE_NUMBER: $ISSUE_TITLE"
# Use printf for proper newline handling in PR body
PR_BODY=$(printf "This pull request addresses issue #%s.\n\n%s\n\nCloses #%s" "$ISSUE_NUMBER" "$ISSUE_URL" "$ISSUE_NUMBER")

PR_URL=$(gh pr create --base main --head "$BRANCH_NAME" --title "$PR_TITLE" --body "$PR_BODY")

if [ -z "$PR_URL" ]; then
    echo "Error: Failed to create pull request"
    exit 1
fi

echo "✓ Created pull request: $PR_TITLE"
echo "  URL: $PR_URL"

# --- Cleanup: Switch back to main branch ---
echo "Switching back to main branch..."
git checkout main
echo "✓ Switched back to main branch"

echo ""
echo "========================================="
echo "Summary:"
echo "  Issue:  #$ISSUE_NUMBER - $ISSUE_TITLE"
echo "  Branch: $BRANCH_NAME"
echo "  PR:     $PR_URL"
echo "========================================="
```
