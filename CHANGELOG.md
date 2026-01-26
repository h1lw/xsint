# Changelog

All notable changes to KISS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Async plugin architecture with AsyncBasePlugin
- AsyncOSINTEngine for high-performance scanning
- Strict query parser with comprehensive validation
- Plugin template system with clear documentation
- Professional GitHub repository structure
- Comprehensive development documentation

### Changed
- Updated requirements.txt with async dependencies
- Migrated to modern Python packaging structure

### Deprecated
- Sync BasePlugin (still supported but deprecated for new plugins)

### Removed
- Legacy xsint-test.py file moved to examples/
- Demo files moved to examples/ directory

### Fixed
- Linting issues in existing codebase
- Import path problems

### Security
- Improved API key handling in async plugins
- Enhanced input validation in query parser

## [2.0.0] - 2025-01-25

### Added
- Complete async plugin system
- Structured query syntax support (planned)
- Comprehensive plugin development templates
- Professional documentation structure
- GitHub Actions CI/CD pipeline
- Strict validation and error handling

### Changed
- Complete architecture modernization
- Async-first development approach
- Enhanced security and performance

### Migration Guide

#### For Plugin Developers
```python
# Old way (sync)
from kiss.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    def scan(self, target: str, scan_type: str, progress_callback):
        # Sync implementation
        pass

# New way (async)
from kiss.plugins.async_base import AsyncBasePlugin

class MyPlugin(AsyncBasePlugin):
    async def scan_async(self, target: str, scan_type: str, progress_callback):
        # Async implementation
        pass
```

#### For Users
```bash
# Installation now includes async dependencies
pip install -r requirements.txt

# Backward compatibility maintained
python -m kiss user@example.com  # Still works
```

## [1.0.0] - 2024-01-XX

### Added
- Basic OSINT functionality
- Plugin architecture
- Multi-input support
- TUI interface
- Email, phone, IP, username, address, hash scanning

### Plugin Support
- Have I Been Pwned integration
- IPInfo IP geolocation
- VeriPhone phone validation
- OpenStreetMap address geocoding
- Gravatar email lookup
- Hudson Rock stealer malware detection

### Core Features
- Modular plugin system
- Configuration management
- Rate limiting
- Error handling
- Progress reporting

---

## Version History Summary

- **2.0.0**: Modern async architecture with strict validation
- **1.0.0**: Initial release with basic OSINT capabilities

For more detailed information about each release, see the [Release Documentation](docs/RELEASES.md).