# Contributing to AI GitHub Action 🤖

Thank you for your interest in contributing to AI GitHub Action! This document provides guidelines and instructions to help you get started.

## 🚀 Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/ai-github-action.git
   cd ai-github-action
   ```
3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes**
5. **Test your changes**
6. **Commit with clear messages**
7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create a pull request**

## 🛠️ Development Environment

We use uv for dependency management with pyproject.toml:

```bash
# Install uv if not already installed
# curl -LsSf https://astral.sh/uv/install.sh | sh

```

## 🧪 Testing

We use pytest for testing:

```bash
# Run all tests
make test

# Run specific tests
uv run pytest tests/test_pr_review.py

# Run tests with coverage report
uv run pytest --cov=src
```

## 📝 Code Style

We follow these style guidelines:

- **PEP 8** for Python code style
- **Type hints** for all function signatures
- **Docstrings** for all public functions and classes
- **Black** for code formatting
- **isort** for import sorting

Run code quality checks:

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Check typing
make mypy
```

## 🏗️ Project Structure

```
ai-github-action/
├── src/                  # Source code
│   ├── actions/          # GitHub Action implementations
│   ├── github_agents/    # AI agent implementations
│   ├── context/          # GitHub context handling
│   ├── tools/            # Tools for agents
│   └── main.py           # Entry point
├── tests/                # Test suite
├── examples/             # Example workflows
└── docs/                 # Documentation
```

## 🔄 GitHub Actions Integration

This project is designed as a GitHub Action. When making changes, consider:

- **Action inputs** defined in `action.yml`
- **Docker execution** environment
- **GitHub API** interactions
- **Permissions** required for different operations

## 🧠 AI Integration

When working with the AI components:

- Keep prompt engineering clear and focused
- Consider token usage and model limitations
- Test with different types of inputs
- Document any model-specific behavior

## 🚀 Adding New Features

### Adding a New Action Type

1. Create a new Python module in `src/actions/`
2. Implement the corresponding agent in `src/github_agents/`
3. Add any necessary tools in `src/tools/`
4. Update `main.py` to handle the new action type
5. Add tests for the new functionality
6. Update documentation and example workflows
7. Add an example workflow file in `examples/`

### Enhancing Existing Actions

1. Identify the relevant files in `src/actions/` and `src/github_agents/`
2. Make your enhancements with appropriate tests
3. Update the documentation to reflect the changes

## 📊 Release Process

1. Update the version in `pyproject.toml`
2. Update `CHANGELOG.md` with the new version and changes
3. Create a pull request for the release
4. Once merged, create a new release on GitHub with appropriate tags

## 🙏 Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## 📜 License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

---

If you have any questions, feel free to open an issue or start a discussion. Happy coding! 🎉