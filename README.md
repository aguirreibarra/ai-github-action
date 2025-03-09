# AI GitHub Action

> GitHub Actions powered by the AI Agents framework

## Overview

AI GitHub Action leverages the AI Agents framework to create intelligent GitHub Actions that can analyze pull requests, issues, and code repositories. These actions use OpenAI's API to provide insightful feedback, automated code reviews, and helpful responses to issues.

## Features

- Automated PR reviews with code quality feedback
- Issue analysis and suggested responses
- Code scanning for security vulnerabilities and best practices
- Repository statistics and insights
- Customizable AI prompts for different contexts
- Poetry dependency management for consistent environments
- Update existing PR review comments instead of creating new ones

## Usage

### Pull Request Review Action

Add this to your workflow file:

```yaml
name: AI PR Review

on:
  pull_request:
    types: [opened, synchronize]
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.github/**'

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: AI PR Review
        uses: aguirreibarra/ai-github-action@main
        with:
          # Core configuration
          action-type: pr-review
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          
          # Optional configuration
          model: "gpt-4o"
          max-files: 15
          include-patterns: "*.py,*.js,*.ts,*.jsx,*.tsx,*.java"
          exclude-patterns: "**/__tests__/**,**/test/**,**/dist/**"
          auto-approve: "false"
```

The PR Review Action will analyze pull requests and post feedback as a comment. When triggered multiple times on the same PR (e.g., after new commits), it will update its existing comment instead of creating a new one, keeping the PR timeline clean.

#### Advanced PR Review Features

- **Smart File Prioritization**: When a PR contains more files than the `max-files` limit, the action automatically prioritizes files with the most changes
- **Error Handling**: Fails gracefully if specific files can't be retrieved or processed
- **Customizable System Prompt**: Guide the AI's focus towards specific aspects like security, performance, or code style
- **Automatic Approval**: Optionally approve PRs automatically when the AI review is favorable

### Issue Analyzer Action

```yaml
name: AI Issue Analysis

on:
  issues:
    types: [opened]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: AI Issue Analysis
        uses: aguirreibarra/ai-github-action@main
        with:
          action-type: issue-analyze
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Code Scanning Action

```yaml
name: AI Code Scan

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 1'  # Weekly scan

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: AI Code Scan
        uses: aguirreibarra/ai-github-action@main
        with:
          action-type: code-scan
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Configuration

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `action-type` | Type of action (pr-review, issue-analyze, code-scan) | Yes | - |
| `openai-api-key` | OpenAI API key | Yes | - |
| `github-token` | GitHub token for API access | Yes | - |
| `model` | OpenAI model to use | No | gpt-4o-mini |
| `custom-prompt` | Custom system prompt for the AI | No | - |
| `max-files` | Maximum files to review in PR | No | 10 |
| `include-patterns` | Glob patterns for files to include | No | - |
| `exclude-patterns` | Glob patterns for files to exclude | No | - |
| `auto-approve` | Automatically approve PRs with favorable reviews | No | false |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | No | INFO |

## Debugging with LOG_LEVEL

You can control the verbosity of logs by setting the `LOG_LEVEL` environment variable in your workflow:

```yaml
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: AI PR Review
        uses: aguirreibarra/ai-github-action@main
        with:
          action-type: pr-review
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
        env:
          LOG_LEVEL: DEBUG  # Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL
```

- Use `DEBUG` for maximum verbosity when troubleshooting issues
- Use `INFO` for normal operations (default)
- Use `WARNING` or `ERROR` to reduce log output in production environments

## Automatic PR Approval

When the `auto-approve` parameter is set to `true`, the action will allow the AI to directly approve pull requests that it determines meet quality standards. Rather than relying on simplistic text pattern matching, the AI will explicitly call the approval tool when it deems a PR ready to merge.

```yaml
name: AI PR Review with Auto-Approval

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
          
      - name: AI PR Review
        uses: aguirreibarra/ai-github-action@main
        with:
          action-type: pr-review
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-approve: true
```

Note: For automatic approval to work, the GitHub token must have sufficient permissions to submit pull request reviews with approval.

## Development

This project is based on the [AI Agents framework](https://github.com/aguirreibarra/ai-agents) and adapted for GitHub Actions.

### Local Development

```bash
# Clone the repository
git clone https://github.com/aguirreibarra/ai-github-action.git
cd ai-github-action

# Install Poetry if you don't have it
# pip install poetry

# Install dependencies using Poetry
poetry install

# Activate the virtual environment
poetry shell
```

## Adapting from AI Agents

This project adapts core functionality from the AI Agents framework:

1. **Agent Architecture**:
   - Reuses the OpenAI integration pattern
   - Replaces Telegram interface with GitHub API
   - Adapts tools for GitHub-specific functionality

2. **Conversation Model**:
   - Maintains the conversation flow with history
   - Customizes system prompts for GitHub contexts
   - PR reviews, issues, and code scans become conversation contexts

3. **Tool System**:
   - Adapts Tool class pattern for GitHub operations
   - Creates GitHub-specific tools for repository interaction
   - Implements file analysis tools for code review

4. **GitHub Integration**:
   - Uses GitHub API through PyGithub
   - Handles GitHub Actions event context
   - Posts comments back to PRs and issues

## Required Modifications to AI Agents

To better support this use case, the following modifications to the AI Agents project would be beneficial:

1. More modular agent interface that can be swapped (Telegram, GitHub, CLI)
2. Separate core AI functionality from the delivery mechanism
3. Extended tool registration system for different contexts
4. Common utilities for parsing and handling code files
5. Context-specific prompt libraries

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

[MIT License](LICENSE)