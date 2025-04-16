# Contributing to Jyra

Thank you for your interest in contributing to Jyra! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with the following information:

- A clear, descriptive title
- A detailed description of the bug
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Your environment (OS, Python version, etc.)

### Suggesting Features

If you have an idea for a new feature, please create an issue on GitHub with the following information:

- A clear, descriptive title
- A detailed description of the feature
- Why this feature would be useful
- Any implementation ideas you have

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure your changes don't break existing functionality
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Create a new Pull Request

## Development Setup

Follow the instructions in [GETTING_STARTED.md](docs/GETTING_STARTED.md) to set up your development environment.

## Coding Standards

- Follow PEP 8 style guidelines for Python code
- Write docstrings for all functions, classes, and modules
- Include appropriate error handling
- Write tests for new functionality

## Testing

Before submitting a pull request, make sure to run the tests:

```bash
python run_tests.py --type unit
python run_tests.py --type integration
```

## Documentation

If you're adding new features or making changes to existing ones, please update the relevant documentation.

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in the present tense (e.g., "Add feature" not "Added feature")
- Reference issue numbers if applicable (e.g., "Fix #123: Add feature")

## Branch Naming

- Use `feature/` prefix for new features
- Use `bugfix/` prefix for bug fixes
- Use `docs/` prefix for documentation changes
- Use `refactor/` prefix for code refactoring

## Review Process

All pull requests will be reviewed by the project maintainers. We may suggest changes or improvements before merging.

## License

By contributing to Jyra, you agree that your contributions will be licensed under the project's MIT License.

Thank you for contributing to Jyra!
