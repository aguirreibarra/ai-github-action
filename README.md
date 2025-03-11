# AI GitHub Action

> GitHub Actions powered by the AI Agents framework

## Overview

AI GitHub Action leverages the AI Agents framework to create intelligent GitHub Actions that can analyze pull requests, issues, and code repositories. These actions use OpenAI's API to provide insightful feedback, automated code reviews, and helpful responses to issues.

## Features

- Automated PR reviews with code quality feedback
- Issue analysis and suggested responses
- Code scanning for security vulnerabilities and best practices
- Customizable AI prompts for different contexts

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
  pr-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: AI PR Review
        uses: aguirreibarra/ai-github-action@main
        with:
          action-type: pr-review
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

The PR Review Action will analyze pull requests and post feedback as a comment. When triggered multiple times on the same PR (e.g., after new commits), it will update its existing comment instead of creating a new one, keeping the PR timeline clean.

#### Advanced PR Review Features

- **Smart File Prioritization**: When a PR contains more files than the `max-files` limit, the action automatically prioritizes files with the most changes
- **Customizable System Prompt**: Guide the AI's focus towards specific aspects like security, performance, or code style
- **Automatic Approval**: Optionally approve PRs automatically when the AI review is favorable

### Issue Analyzer Action

> **Warning**  
> This action is currently under construction and may not be fully functional

```yaml
name: AI Issue Analysis

on:
  issues:
    types: [opened]

jobs:
  analyze:
    runs-on: ubuntu-latest
    if: github.event.action == 'opened' || contains(github.event.issue.labels.*.name, 'needs-triage')
    steps:
      - name: AI Issue Analysis
        uses: aguirreibarra/ai-github-action@main
        with:
          action-type: issue-analyze
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Remove needs-triage label
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            try {
              await github.rest.issues.removeLabel({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                name: 'needs-triage'
              });
            } catch (e) {
              // Label might not exist, that's okay
            }
```

### Code Scanning Action

> **Warning**  
> This action is currently under construction and may not be fully functional

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

[MIT License](LICENSE)