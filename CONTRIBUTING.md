# Contributing to KISS

Thank you for your interest in contributing to KISS! This guide will help you get started.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Standards](#code-standards)
3. [Testing](#testing)
4. [Pull Request Process](#pull-request-process)
5. [Plugin Development](#plugin-development)
6. [Documentation](#documentation)

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Make (optional, for make commands)

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/kiss.git
cd kiss

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Verify installation
python -m kiss --version
```

### Development Tools

- **Black**: Code formatting
- **Flake8**: Linting
- **isort**: Import sorting
- **MyPy**: Type checking
- **pytest**: Testing

## Code Standards

### Python Style

We follow PEP 8 with some additional guidelines:

```python
# Use type hints
def scan_email(target: str, progress_callback: Callable[[float], None]) -> ScanResult:
    pass

# Use docstrings
def scan_email(target: str, progress_callback: Callable[[float], None]) -> ScanResult:
    """
    Scan email address for intelligence.
    
    Args:
        target: Email address to scan
        progress_callback: Progress reporting function
        
    Returns:
        ScanResult with findings
    """
    pass

# Import organization
import os
import sys
from typing import Any, Callable, Dict, List, Optional

import requests
from kiss.constants import ScanType
from kiss.models import ScanResult
```

### Code Formatting

```bash
# Format code
black kiss/ isort kiss/

# Check formatting
black --check kiss/ isort --check-only kiss/

# Lint code
flake8 kiss/

# Type check
mypy kiss/
```

### Error Handling

```python
# Always handle exceptions
async def scan_async(self, target: str, scan_type: str, progress_callback: Callable[[float], None]) -> List[Dict[str, Any]]:
    results = []
    
    try:
        # Your logic here
        response = await self._make_request(url)
        data = await response.json()
        results.extend(self._process_data(data))
        
    except aiohttp.ClientError as e:
        results.append(self._create_result(
            "Network Error",
            f"Connection failed: {str(e)}",
            threat_level="HIGH"
        ))
    except ValueError as e:
        results.append(self._create_result(
            "Data Error",
            f"Invalid response format: {str(e)}",
            threat_level="MEDIUM"
        ))
    except Exception as e:
        results.append(self._create_result(
            "Error",
            f"Unexpected error: {str(e)}",
            threat_level="HIGH"
        ))
    
    return results
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kiss --cov-report=html

# Run specific test file
pytest tests/test_scanner.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_scanner.py::test_email_detection
```

### Writing Tests

```python
# tests/test_my_plugin.py
import pytest
from unittest.mock import AsyncMock, patch
from kiss.plugins.my_category.my_plugin import MyPlugin

@pytest.mark.asyncio
async def test_my_plugin_success():
    """Test successful plugin execution."""
    config = get_config()
    plugin = MyPlugin(config)
    
    # Mock API response
    with patch.object(plugin, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value.status = 200
        mock_request.return_value.json = AsyncMock(return_value={"result": "test"})
        
        results = await plugin.scan_async("test@example.com", "EMAIL", lambda x: None)
        
        assert len(results) > 0
        assert any(r["label"] == "Analysis Result" for r in results)

@pytest.mark.asyncio
async def test_my_plugin_api_error():
    """Test plugin behavior when API fails."""
    config = get_config()
    plugin = MyPlugin(config)
    
    with patch.object(plugin, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = None  # API unavailable
        
        results = await plugin.scan_async("test@example.com", "EMAIL", lambda x: None)
        
        # Should handle error gracefully
        assert len(results) > 0
        assert any("Error" in r["label"] for r in results)

@pytest.mark.asyncio
async def test_my_plugin_not_configured():
    """Test plugin behavior when API key missing."""
    config = get_config()
    plugin = MyPlugin(config)
    
    # Mock missing API key
    with patch.object(plugin, 'is_configured', return_value=False):
        results = await plugin.scan_async("test@example.com", "EMAIL", lambda x: None)
        
        assert len(results) > 0
        assert any("Configuration" in r["label"] for r in results)
```

### Test Coverage

Aim for >90% test coverage. Check coverage report in `htmlcov/index.html`.

## Pull Request Process

### Branch Strategy

- `main`: Stable releases
- `develop`: Development branch
- `feature/branch-name`: Feature development
- `bugfix/branch-name`: Bug fixes

### PR Checklist

Before submitting a PR:

- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Documentation added/updated as needed
- [ ] Type hints added where appropriate
- [ ] Error handling implemented appropriately
- [ ] New tests added for new functionality
- [ ] Existing tests still pass
- [ ] Edge cases tested
- [ ] No hardcoded credentials or sensitive data
- [ ] Performance impact considered
- [ ] Security implications considered

### Submitting PR

```bash
# Create feature branch
git checkout -b feature/my-new-feature

# Make your changes
# ... commit changes ...

# Push to your fork
git push origin feature/my-new-feature

# Create pull request
# Use the template at .github/PULL_REQUEST_TEMPLATE.md
```

## Plugin Development

See [Plugin Development Guide](docs/PLUGIN_DEVELOPMENT.md) for comprehensive instructions.

### Quick Start

```bash
# Create plugin from template
cp kiss/plugins/templates/email_intelligence_template.py kiss/plugins/my_category/my_plugin.py

# Edit metadata
# Implement scan_async method
# Add tests

# Test plugin
python -c "
from kiss.plugins.my_category.my_plugin import MyPlugin
from kiss.config import get_config
config = get_config()
plugin = MyPlugin(config)
print(plugin.get_metadata())
"
```

### Plugin Requirements

- Inherit from `AsyncBasePlugin` (recommended)
- Implement `get_metadata()` and `scan_async()`
- Handle all exceptions gracefully
- Provide meaningful error messages
- Use proper threat levels (LOW, MEDIUM, HIGH, CRITICAL)
- Include comprehensive tests

## Documentation

### Updating Documentation

- **README.md**: Update for major features
- **PLUGIN_DEVELOPMENT.md**: Update for plugin API changes
- **docs/**: Add detailed documentation for new features
- **Code docstrings**: Keep documentation in code

### Documentation Style

```markdown
# Section Header
Section content here.

### Subsection
More specific content.

```python
# Code example
def example():
    pass
```

- Bullet points
- Another bullet point
```

## Performance Guidelines

### Async Programming

- Use `async/await` for I/O operations
- Never block the event loop
- Use `asyncio.gather()` for concurrent operations

### Resource Management

- Use connection pooling (provided by AsyncBasePlugin)
- Respect rate limits
- Clean up resources in `async close()`

### Memory Usage

- Avoid loading large datasets into memory
- Use streaming for large responses
- Implement pagination for large result sets

## Security Guidelines

### Input Validation

```python
# Always validate inputs
def scan_email(self, target: str, scan_type: str, progress_callback):
    if not isinstance(target, str):
        raise TypeError("Target must be a string")
    
    if scan_type not in self.metadata.supported_scan_types:
        return [self._create_result(
            "Error",
            f"Unsupported scan type: {scan_type}",
            threat_level="HIGH"
        )]
```

### API Key Handling

- Never hardcode API keys
- Use environment variables or config files
- Don't log API keys or sensitive data
- Mask sensitive data in error messages

### Dependency Management

- Keep dependencies to minimum
- Review security of dependencies regularly
- Use pinned versions for security-critical deps

## Release Process

### Version Management

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Security review completed
- [ ] Performance testing completed
- [ ] Integration tests passing

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check docs/ folder first
- **Examples**: See examples/ folder for usage patterns

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- git commit history

Thank you for contributing to KISS! Your contributions help make OSINT tools better for everyone.