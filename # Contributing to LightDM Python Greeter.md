# Contributing to LightDM Python Greeter

First off, thank you for considering contributing to LightDM Python Greeter! It's people like you that make this project such a great tool. 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [your-email@example.com].

### Our Standards

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Ubuntu 20.04+ or similar Linux distribution
- Git
- Docker (optional, for containerized development)

### Setting Up Development Environment

1. **Fork the repository**
   ```bash
   # Click the 'Fork' button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/lightdm-python-greeter.git
   cd lightdm-python-greeter
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/original-repo/lightdm-python-greeter.git
   ```

4. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pre-commit install
   ```

6. **Or use Docker**
   ```bash
   make build
   make run
   ```

## How Can I Contribute?

### Reporting Bugs 🐛

Before creating bug reports, please check existing issues to avoid duplicates.

**How to Submit a Good Bug Report:**

1. Use a clear and descriptive title
2. Describe the exact steps to reproduce the problem
3. Provide specific examples
4. Describe the behavior you observed and expected
5. Include screenshots if relevant
6. Include your environment details:
   - OS version
   - Python version
   - LightDM version
   - Relevant configuration

**Bug Report Template:**
```markdown
### Description
[Clear description of the bug]

### Steps to Reproduce
1. [First step]
2. [Second step]
3. [...]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.9.5]
- LightDM: [e.g., 1.30.0]

### Additional Context
[Any other relevant information]
```

### Suggesting Enhancements 💡

Enhancement suggestions are tracked as GitHub issues.

**How to Submit a Good Enhancement Suggestion:**

1. Use a clear and descriptive title
2. Provide a detailed description of the proposed enhancement
3. Explain why this enhancement would be useful
4. List any alternative solutions you've considered

### Contributing Code 💻

#### Types of Contributions

- **Bug fixes**: Fix reported issues
- **Features**: Implement new functionality
- **Performance**: Optimize existing code
- **Documentation**: Improve or add documentation
- **Tests**: Add missing tests
- **Refactoring**: Improve code quality

## Development Process

### Branching Strategy

We use Git Flow for branch management:

- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent fixes for production
- `release/*` - Release preparation

### Creating a Feature Branch

```bash
# Update your local develop branch
git checkout develop
git pull upstream develop

# Create your feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Commit your changes
git add .
git commit -m "feat: add amazing feature"

# Push to your fork
git push origin feature/your-feature-name
```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**
```bash
git commit -m "feat(auth): add biometric authentication support"
git commit -m "fix(ui): correct password field validation"
git commit -m "docs: update installation instructions"
```

## Style Guidelines

### Python Style Guide

We follow PEP 8 with some modifications:

```python
# Good
class PasswordValidator:
    """Validates user passwords."""
    
    def __init__(self, min_length: int = 8):
        self.min_length = min_length
    
    def validate(self, password: str) -> bool:
        """
        Validate a password.
        
        Args:
            password: The password to validate
            
        Returns:
            True if valid, False otherwise
        """
        if len(password) < self.min_length:
            return False
        return True

# Bad
class password_validator:
    def __init__(self,minLength=8):
        self.minLength=minLength
    def Validate(self,pwd):
        if len(pwd)<self.minLength: return False
        return True
```

### Code Formatting

- Use `black` for automatic formatting
- Use `isort` for import sorting
- Line length: 88 characters (Black default)
- Use type hints where possible

```bash
# Format your code
black src/ tests/
isort src/ tests/
```

### Docstrings

Use Google style docstrings:

```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of function.
    
    Longer description if needed, explaining the function's
    behavior in detail.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: If param2 is negative
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {'status': 'success'}
    """
    pass
```

## Testing Guidelines

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

```python
def test_password_validator_accepts_valid_password():
    """Test that valid passwords are accepted."""
    # Arrange
    validator = PasswordValidator(min_length=8)
    valid_password = "ValidPass123!"
    
    # Act
    result = validator.validate(valid_password)
    
    # Assert
    assert result is True
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_security.py

# Run in Docker
make test
```

### Test Categories

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Test response times and resource usage

## Documentation

### Code Documentation

- All public functions/classes must have docstrings
- Use inline comments for complex logic
- Keep README.md up to date
- Update CHANGELOG.md for all changes

### User Documentation

Located in `docs/`:

- Installation guides
- Configuration reference
- Troubleshooting guides
- API documentation

### Building Documentation

```bash
cd docs/
make html
# View at docs/_build/html/index.html
```

## Pull Request Process

### Before Submitting

1. **Update your branch**
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```

2. **Run tests**
   ```bash
   pytest
   make lint
   ```

3. **Update documentation**
   - Update README.md if needed
   - Add/update docstrings
   - Update CHANGELOG.md

4. **Check your changes**
   ```bash
   git diff upstream/develop
   ```

### Submitting a Pull Request

1. Push your changes to your fork
2. Go to the original repository on GitHub
3. Click "New Pull Request"
4. Select your fork and branch
5. Fill in the PR template:

```markdown
## Description
[Brief description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Coverage maintained/improved

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Commits follow conventional format

## Related Issues
Fixes #(issue number)

## Screenshots (if applicable)
[Add screenshots]
```

### Review Process

1. Automated checks run (linting, tests, security)
2. Code review by maintainers
3. Address feedback
4. Approval and merge

### After Merge

- Delete your feature branch
- Update your local repository:
  ```bash
  git checkout develop
  git pull upstream develop
  git push origin develop
  ```

## Community

### Getting Help

- **GitHub Issues**: For bugs and features
- **Discussions**: For questions and ideas
- **Discord**: [Join our server](https://discord.gg/example)
- **Email**: support@example.com

### Recognition

Contributors are recognized in:
- [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Release notes
- Project documentation

### Becoming a Maintainer

Active contributors may be invited to become maintainers. Criteria:
- Consistent high-quality contributions
- Good understanding of the codebase
- Helpful in community discussions
- Commitment to project values

## Tips for Success

1. **Start Small**: Begin with documentation or small bug fixes
2. **Ask Questions**: Don't hesitate to ask for clarification
3. **Be Patient**: Review may take time
4. **Be Receptive**: Accept feedback gracefully
5. **Have Fun**: Enjoy the process of contributing!

## Resources

- [Python Style Guide (PEP 8)](https://www.python.org/dev/peps/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Writing Good Commit Messages](https://chris.beams.io/posts/git-commit/)
- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)

---

Thank you for contributing to LightDM Python Greeter! 🚀

Your contributions, no matter how small, make a difference. We look forward to working with you!