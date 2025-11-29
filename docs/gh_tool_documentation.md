# gh CLI Tool Documentation

## Introduction

`gh` is GitHub's official command-line interface. It brings GitHub to your terminal, allowing you to manage repositories, issues, pull requests, releases, and more directly from your command line. It's designed to be a fast, seamless, and scriptable way to interact with GitHub.

## Installation

Installation typically involves using a package manager specific to your operating system (e.g., Homebrew on macOS, apt on Debian/Ubuntu, yum on Fedora/RHEL). Refer to the official GitHub CLI documentation for the most up-to-date installation instructions: [https://cli.github.com/manual/installation](https://cli.github.com/manual/installation)

## Authentication

Before using `gh` to interact with your GitHub account, you need to authenticate. This usually involves running the `gh auth login` command and following the prompts to connect your account.

```bash
gh auth login
```

## Core Commands

Here are some of the main command categories available in `gh`:

*   **`auth`**: Authenticate `gh` and Git with GitHub.
*   **`browse`**: Open repositories, issues, pull requests, and more in the web browser.
*   **`codespace`**: Connect to and manage codespaces.
*   **`gist`**: Manage Gists.
*   **`issue`**: Manage issues in repositories.
*   **`org`**: Manage GitHub organizations.
*   **`pr`**: Manage pull requests.
*   **`project`**: Work with GitHub Projects.
*   **`release`**: Manage releases for your repositories.
*   **`repo`**: Manage repositories (create, clone, view, etc.).

## GitHub Actions Commands

*   **`cache`**: Manage GitHub Actions caches.
*   **`run`**: View details about workflow runs.
*   **`workflow`**: View details about GitHub Actions workflows.

## Additional Commands

*   **`agent-task`**: Work with agent tasks (preview)
*   **`alias`**: Create command shortcuts.
*   **`api`**: Make an authenticated GitHub API request.
*   **`completion`**: Generate shell completion scripts.
*   **`config`**: Manage configuration for `gh`.
*   **`extension`**: Manage `gh` extensions.
*   **`search`**: Search for repositories, issues, and pull requests.
*   **`secret`**: Manage GitHub secrets.
*   **`status`**: Print information about relevant issues, pull requests, and notifications.

## Examples

Here are some common usage examples:

*   Create a new GitHub issue:
    ```bash
    gh issue create
    ```
*   Clone a repository:
    ```bash
    gh repo clone cli/cli
    ```
*   Checkout a pull request:
    ```bash
    gh pr checkout 321
    ```

For more detailed information about any specific command, use `gh <command> <subcommand> --help`. For instance, to learn more about `gh issue`, run:
```bash
gh issue --help
```

## Detailed Command Reference

### `gh auth` - Authenticate gh and git with GitHub

*   **`login`**: Log in to a GitHub account
*   **`logout`**: Log out of a GitHub account
*   **`refresh`**: Refresh stored authentication credentials
*   **`setup-git`**: Setup git with GitHub CLI
*   **`status`**: Display active account and authentication state on each known GitHub host
*   **`switch`**: Switch active GitHub account
*   **`token`**: Print the authentication token gh uses for a hostname and account

### `gh browse` - Open items in the web browser

*   **Options**
    *   **`-b, --branch string`**: Select another branch by passing in the branch name.
    *   **`-c, --commit string[="last"]`**: Select another commit by passing in the commit SHA, default is the last commit.
    *   **`-n, --no-browser`**: Print destination URL instead of opening the browser.
    *   **`-p, --projects`**: Open repository projects.
    *   **`-r, --releases`**: Open repository releases.
    *   **`-R, --repo [HOST/]OWNER/REPO`**: Select another repository using the `[HOST/]OWNER/REPO` format.
    *   **`-s, --settings`**: Open repository settings.
    *   **`-w, --wiki`**: Open repository wiki.
*   **Arguments**
    *   A browser location can be specified using arguments in the following format:
        *   by number for issue or pull request, e.g. "123"; or
        *   by path for opening folders and files, e.g. "cmd/gh/main.go"; or
        *   by commit SHA.

### `gh codespace` - Connect to and manage codespaces

*   **`code`**: Open a codespace in Visual Studio Code
*   **`cp`**: Copy files between local and remote file systems
*   **`create`**: Create a codespace
*   **`delete`**: Delete codespaces
    *   **`edit`**: Edit a codespace
    *   **`jupyter`**: Open a codespace in JupyterLab
    *   **`list`**: List codespaces
    *   **`logs`**: Access codespace logs
    *   **`ports`**: List ports in a codespace
    *   **`rebuild`**: Rebuild a codespace
    *   **`ssh`**: SSH into a codespace
    *   **`stop`**: Stop a running codespace
    *   **`view`**: View details about a codespace

### `gh gist` - Work with GitHub gists

*   **`clone`**: Clone a gist locally
    *   **`create`**: Create a new gist
    *   **`delete`**: Delete a gist
    *   **`edit`**: Edit one of your gists
    *   **`list`**: List your gists
    *   **`rename`**: Rename a file in a gist
    *   **`view`**: View a gist

### `gh issue` - Work with GitHub issues

*   **General Commands**
    *   **`create`**: Create a new issue
    *   **`list`**: List issues in a repository
    *   **`status`**: Show status of relevant issues
*   **Targeted Commands**
    *   **`close`**: Close issue
    *   **`comment`**: Add a comment to an issue
    *   **`delete`**: Delete issue
    *   **`develop`**: Manage linked branches for an issue
    *   **`edit`**: Edit issues
    *   **`lock`**: Lock issue conversation
    *   **`pin`**: Pin a issue
    *   **`reopen`**: Reopen issue
    *   **`transfer`**: Transfer issue to another repository
    *   **`unlock`**: Unlock issue conversation
    *   **`unpin`**: Unpin a issue
    *   **`view`**: View an issue

### `gh org` - Work with GitHub organizations

*   **General Commands`**:
    *   **`list`**: List organizations for the authenticated user.

### `gh project` - Work with GitHub Projects

*   **`close`**: Close a project
    *   **`copy`**: Copy a project
    *   **`create`**: Create a project
    *   **`delete`**: Delete a project
    *   **`edit`**: Edit a project
    *   **`field-create`**: Create a field in a project
    *   **`field-delete`**: Delete a field in a project
    *   **`field-list`**: List the fields in a project
    *   **`item-add`**: Add a pull request or an issue to a project
    *   **`item-archive`**: Archive an item in a project
    *   **`item-create`**: Create a draft issue item in a project
    *   **`item-delete`**: Delete an item from a project by ID
    *   **`item-edit`**: Edit an item in a project
    *   **`item-list`**: List the items in a project
    *   **`link`**: Link a project to a repository or a team
    *   **`list`**: List the projects for an owner
    *   **`mark-template`**: Mark a project as a template
    *   **`unlink`**: Unlink a project from a repository or a team
    *   **`view`**: View a project

### `gh pr` - Work with GitHub pull requests

*   **General Commands**
    *   **`create`**: Create a pull request
    *   **`list`**: List pull requests in a repository
    *   **`status`**: Show status of relevant pull requests
*   **Targeted Commands**
    *   **`checkout`**: Check out a pull request in git
    *   **`checks`**: Show CI status for a single pull request
    *   **`close`**: Close a pull request
    *   **`comment`**: Add a comment to a pull request
    *   **`diff`**: View changes in a pull request
    *   **`edit`**: Edit a pull request
    *   **`lock`**: Lock pull request conversation
    *   **`merge`**: Merge a pull request
    *   **`ready`**: Mark a pull request as ready for review
    *   **`reopen`**: Reopen a pull request
    *   **`review`**: Add a review to a pull request
    *   **`unlock`**: Unlock pull request conversation
    *   **`update-branch`**: Update a pull request branch
    *   **`view`**: View a pull request

### `gh release` - Manage releases

*   **General Commands**
    *   **`create`**: Create a new release
    *   **`list`**: List releases in a repository
*   **Targeted Commands**
    *   **`delete`**: Delete a release
    *   **`delete-asset`**: Delete an asset from a release
    *   **`download`**: Download release assets
    *   **`edit`**: Edit a release
    *   **`upload`**: Upload assets to a release
    *   **`verify`**: Verify the attestation for a release
    *   **`verify-asset`**: Verify that a given asset originated from a release
    *   **`view`**: View information about a release

### `gh repo` - Work with GitHub repositories

*   **General Commands**
    *   **`create`**: Create a new repository
    *   **`list`**: List repositories owned by user or organization
*   **Targeted Commands**
    *   **`archive`**: Archive a repository
    *   **`autolink`**: Manage autolink references
    *   **`clone`**: Clone a repository locally
    *   **`delete`**: Delete a repository
    *   **`deploy-key`**: Manage deploy keys in a repository
    **`edit`**: Edit repository settings
    **`fork`**: Create a fork of a repository
    **`gitignore`**: List and view available repository gitignore templates
    **`license`**: Explore repository licenses
    **`rename`**: Rename a repository
    **`set-default`**: Configure default repository for this directory
    **`sync`**: Sync a repository
    **`unarchive`**: Unarchive a repository
    **`view`**: View a repository

### `gh cache` - Work with GitHub Actions caches

*   **`delete`**: Delete GitHub Actions caches
*   **`list`**: List GitHub Actions caches

### `gh run` - List, view, and watch recent workflow runs from GitHub Actions

*   **`cancel`**: Cancel a workflow run
*   **`delete`**: Delete a workflow run
*   **`download`**: Download artifacts generated by a workflow run
*   **`list`**: List recent workflow runs
*   **`rerun`**: Rerun a run
    *   **`view`**: View a summary of a workflow run
    *   **`watch`**: Watch a run until it completes, showing its progress

### `gh workflow` - List, view, and run workflows in GitHub Actions

*   **`disable`**: Disable a workflow
*   **`enable`**: Enable a workflow
    *   **`list`**: List workflows
    *   **`run`**: Run a workflow by creating a workflow_dispatch event
    *   **`view`**: View the summary of a workflow

### `gh agent-task` - Work with agent tasks (preview)

*   **`create`**: Create an agent task (preview)
*   **`list`**: List agent tasks (preview)
    *   **`view`**: View an agent task session (preview)

### `gh alias` - Create command shortcuts

*   **`delete`**: Delete set aliases
*   **`import`**: Import aliases from a YAML file
    *   **`list`**: List your aliases
    *   **`set`**: Create a shortcut for a gh command

### `gh api` - Make an authenticated HTTP request to the GitHub API

*   **Flags**
    *   **`--cache duration`**: Cache the response, e.g. "3600s", "60m", "1h".
    *   **`-F, --field key=value`**: Add a typed parameter in key=value format.
    *   **`-H, --header key:value`**: Add a HTTP request header in key:value format.
    *   **`--hostname string`**: The GitHub hostname for the request (default "github.com").
    *   **`-i, --include`**: Include HTTP response status line and headers in the output.
    *   **`--input file`**: The file to use as body for the HTTP request (use "-" to read from standard input).
    *   **`-q, --jq string`**: Query to select values from the response using jq syntax.
    *   **`-X, --method string`**: The HTTP method for the request (default "GET").
    *   **`--paginate`**: Make additional HTTP requests to fetch all pages of results.
    *   **`-p, --preview strings`**: Opt into GitHub API previews (names should omit '-preview').
    *   **`-f, --raw-field key=value`**: Add a string parameter in key=value format.
    *   **`--silent`**: Do not print the response body.
    *   **`--slurp`**: Use with "--paginate" to return an array of all pages of either JSON arrays or objects.
    *   **`-t, --template string`**: Format JSON output using a Go template; see "gh help formatting".
    *   **`--verbose`**: Include full HTTP request and response in the output.

### `gh attestation` - Download and verify artifact attestations

*   **`download`**: Download an artifact's attestations for offline use
*   **`trusted-root`**: Output trusted_root.jsonl contents, likely for offline verification
*   **`verify`**: Verify an artifact's integrity using attestations

### `gh completion` - Generate shell completion scripts for GitHub CLI commands

*   **Flags**
    *   **`-s, --shell string`**: Shell type: {bash|zsh|fish|powershell}.

### `gh config` - Display or change configuration settings for gh

*   **`clear-cache`**: Clear the cli cache
*   **`get`**: Print the value of a given configuration key
*   **`list`**: Print a list of configuration keys and values
*   **`set`**: Update configuration with a value for the given key

### `gh gpg-key` - Manage GPG keys registered with your GitHub account

*   **`add`**: Add a GPG key to your GitHub account
*   **`delete`**: Delete a GPG key from your GitHub account
*   **`list`**: Lists GPG keys in your GitHub account

### `gh label` - Work with GitHub labels

*   **`clone`**: Clones labels from one repository to another
*   **`create`**: Create a new label
*   **`delete`**: Delete a label from a repository
*   **`edit`**: Edit a label
*   **`list`**: List labels in a repository

### `gh preview` - Preview commands

*   **`prompter`**: Execute a test program to preview the prompter

### `gh ruleset` - Work with GitHub rulesets

*   **`check`**: View rules that would apply to a given branch
*   **`list`**: List rulesets for a repository or organization
*   **`view`**: View information about a ruleset

### `gh search` - Search across all of GitHub

*   **`code`**: Search within code
*   **`commits`**: Search for commits
*   **`issues`**: Search for issues
*   **`prs`**: Search for pull requests
*   **`repos`**: Search for repositories

### `gh secret` - Create or update secrets

*   **`delete`**: Delete secrets
*   **`list`**: List secrets
*   **`set`**: Create or update secrets

### `gh ssh-key` - Manage SSH keys registered with your GitHub account

*   **`add`**: Add an SSH key to your GitHub account
*   **`delete`**: Delete an SSH key from your GitHub account
*   **`list`**: Lists SSH keys in your GitHub account

### `gh status` - Print information about your work on GitHub

*   **Flags**
    *   **`-e, --exclude strings`**: Comma separated list of repos to exclude in owner/name format.
    *   **`-o, --org string`**: Report status within an organization.

### `gh variable` - Create or update variables

*   **`delete`**: Delete variables
*   **`get`**: Get variables
*   **`list`**: List variables
*   **`set`**: Create or update variables