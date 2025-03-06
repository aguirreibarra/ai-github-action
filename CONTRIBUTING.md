# Contributing to AI GitHub Action

Thank you for your interest in contributing to this project!

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/ai-github-action.git`
3. Create a new branch for your feature/fix: `git checkout -b feature-name`
4. Make your changes
5. Test your changes
6. Commit your changes with descriptive commit messages
7. Push to your fork: `git push origin feature-name`
8. Create a pull request

## Development Environment

```bash
# Ensure Poetry is installed
# pip install poetry

# Install all dependencies (including dev dependencies)
poetry install

# Activate the virtual environment
poetry shell

# Run a command within the environment without activating
poetry run pytest
```

## Testing

We use pytest for testing:

```bash
# Run all tests
poetry run pytest
```

## Adapting from AI Agents

This project adapts core functionality from the AI Agents framework. If you're familiar with the AI Agents project, here are the key differences:

1. **Interface**: Instead of Telegram, we use GitHub API
2. **Tools**: GitHub-specific tools instead of general-purpose tools
3. **Actions**: Three main actions (PR review, issue analysis, code scan)
4. **Context**: GitHub event-driven context instead of chat-based

## Repository Structure

- `actions/`: Contains different GitHub Action implementations
- `tools/`: GitHub-specific tool implementations
- `tests/`: Test suite
- `.github/workflows/`: CI/CD workflows

## Style Guidelines

- We follow PEP 8 for Python code style
- Use type hints where possible
- Document functions and classes with docstrings

## Pull Request Process

1. Ensure your code passes all tests
2. Update the documentation if needed
3. Make sure your code is well-tested
4. Create a pull request with a clear description
5. Address any feedback from reviewers

## Testing GitHub Actions Locally

To test GitHub Actions locally:

1. Set up required environment variables:
```bash
export GITHUB_TOKEN=your_token
export OPENAI_API_KEY=your_key
```

2. Create a test event JSON file (e.g., `event.json`):
```json
{
  "repository": {
    "full_name": "owner/repo"
  },
  "pull_request": {
    "number": 123
  }
}
```

3. Run the action directly:
```bash
export GITHUB_EVENT_PATH=./event.json
python main.py
```

## Extending with New Actions

To add a new action type:

1. Create a new class in the `actions/` directory
2. Implement the `run()` method
3. Update the `main.py` file to handle the new action type
4. Add tests for the new action
5. Update documentation

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.