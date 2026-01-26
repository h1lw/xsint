# KISS Plugin Development Guide

This guide provides comprehensive instructions for developing plugins for the KISS OSINT toolkit.

## Table of Contents

1. [Plugin Architecture](#plugin-architecture)
2. [Async vs Sync Plugins](#async-vs-sync-plugins)
3. [Plugin Structure](#plugin-structure)
4. [Development Workflow](#development-workflow)
5. [API Integration](#api-integration)
6. [Error Handling](#error-handling)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Examples](#examples)

## Plugin Architecture

KISS uses a modular plugin architecture that allows for:

- **Async Operations**: Non-blocking HTTP requests for better performance
- **Backward Compatibility**: Sync plugins work with async engine
- **Resource Management**: Automatic connection pooling and rate limiting
- **Configuration**: Centralized API key management
- **Discovery**: Automatic plugin detection and registration

### Core Components

- **AsyncBasePlugin**: Base class for async plugins
- **BasePlugin**: Legacy base class for sync plugins
- **PluginMetadata**: Plugin information and capabilities
- **APIKeyRequirement**: API key configuration
- **AsyncOSINTEngine**: High-performance async scanning engine

## Async vs Sync Plugins

### Async Plugins (Recommended)

**Benefits:**
- Non-blocking I/O
- Higher concurrency
- Better resource utilization
- Faster scan times with hundreds of modules

**When to use:**
- New plugins
- HTTP API integrations
- Performance-critical modules
- Plugins that will scale to many requests

**Example:**
```python
from kiss.plugins.async_base import AsyncBasePlugin, PluginMetadata

class MyAsyncPlugin(AsyncBasePlugin):
    async def scan_async(self, target: str, scan_type: str, progress_callback: Callable[[float], None]) -> List[Dict[str, Any]]:
        # Async implementation
        response = await self._make_request("https://api.example.com/lookup")
        data = await response.json()
        return [self._create_result("Result", data["value"])]
```

### Sync Plugins (Legacy)

**Benefits:**
- Simpler implementation
- No async/await complexity
- Compatible with existing code

**When to use:**
- Simple local processing
- Legacy code migration
- Non-network operations
- Quick prototypes

**Example:**
```python
from kiss.plugins.base import BasePlugin, PluginMetadata

class MySyncPlugin(BasePlugin):
    def scan(self, target: str, scan_type: str, progress_callback: Callable[[float], None]) -> List[Dict[str, Any]]:
        # Sync implementation
        response = self.session.get("https://api.example.com/lookup")
        data = response.json()
        return [self._create_result("Result", data["value"])]
```

## Plugin Structure

### Required Elements

Every plugin must have:

1. **Class Definition**: Inherit from AsyncBasePlugin or BasePlugin
2. **Metadata**: Implement `get_metadata()` method
3. **Scan Method**: Implement `scan_async()` or `scan()` method
4. **File Location**: Proper placement for auto-discovery

### File Structure

```
kiss/plugins/
├── templates/
│   └── email_intelligence_template.py
├── email/
│   ├── __init__.py
│   └── my_email_plugin.py
├── phone/
│   ├── __init__.py
│   └── my_phone_plugin.py
└── username/
    ├── __init__.py
    └── my_username_plugin.py
```

### Plugin Class Template

```python
"""
Plugin Name - Brief Description

Detailed description of what this plugin does,
what APIs it uses, and what information it provides.
"""

from typing import Any, Callable, Dict, List, Optional

from kiss.plugins.async_base import AsyncBasePlugin, PluginMetadata, APIKeyRequirement


class MyPlugin(AsyncBasePlugin):
    """Plugin description."""
    
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="my_plugin",                    # Unique identifier
            display_name="My Plugin",            # Human-readable name
            description="Brief description",     # One-line description
            version="1.0.0",                     # Semantic version
            category="Plugin Category",          # e.g., "Email Intelligence"
            supported_scan_types=["EMAIL"],      # Scan types this plugin handles
            api_key_requirements=[               # API keys needed
                APIKeyRequirement(
                    key_name="api_key",
                    env_var="KISS_MY_PLUGIN_API_KEY",
                    display_name="My Plugin API Key",
                    description="Required for plugin functionality",
                    signup_url="https://api.example.com/signup",
                    is_required=True
                )
            ],
            rate_limit=60,                       # Requests per minute
            timeout=30,                          # Request timeout
            author="Your Name",                  # Plugin author
            dependencies=[],                      # Other plugins required
        )
    
    async def scan_async(
        self,
        target: str,
        scan_type: str,
        progress_callback: Callable[[float], None],
    ) -> List[Dict[str, Any]]:
        """Main scan method implementation."""
        results: List[Dict[str, Any]] = []
        
        # Validate scan type
        if scan_type not in self.metadata.supported_scan_types:
            return [self._create_result(
                "Error",
                f"Unsupported scan type: {scan_type}",
                threat_level="HIGH"
            )]
        
        # Check configuration
        if not self.is_configured():
            return [self._create_result(
                "Configuration",
                "API key not configured",
                threat_level="MEDIUM"
            )]
        
        try:
            # Main plugin logic here
            progress_callback(0.1)
            
            # Example API call
            response = await self._make_request(
                "https://api.example.com/endpoint",
                params={"target": target}
            )
            
            progress_callback(0.5)
            
            if response and response.status == 200:
                data = await response.json()
                
                # Process results
                results.append(self._create_result(
                    "Analysis Result",
                    data.get("result", "No data"),
                    source="API"
                ))
            
            progress_callback(1.0)
            
        except Exception as e:
            results.append(self._create_result(
                "Error",
                f"Plugin failed: {str(e)}",
                threat_level="HIGH"
            ))
        
        return results
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone KISS repository
git clone https://github.com/yourusername/kiss.git
cd kiss

# Install development dependencies
pip install -r requirements-dev.txt

# Create plugin directory
mkdir -p kiss/plugins/my_category
touch kiss/plugins/my_category/__init__.py
```

### 2. Create Plugin File

```bash
# Create plugin from template
cp kiss/plugins/templates/email_intelligence_template.py kiss/plugins/my_category/my_plugin.py
```

### 3. Implement Plugin Logic

1. **Update Metadata**: Modify `get_metadata()` with your plugin details
2. **Implement Scan Logic**: Add your main functionality in `scan_async()`
3. **Add API Integration**: Use `_make_request()` for HTTP calls
4. **Handle Errors**: Graceful error handling with meaningful messages
5. **Test Progress**: Update `progress_callback()` appropriately

### 4. Test Plugin

```python
# Test your plugin
from kiss.plugins.my_category.my_plugin import MyPlugin
from kiss.config import get_config

config = get_config()
plugin = MyPlugin(config)

# Test scan
results = await plugin.scan_async("test@example.com", "EMAIL", lambda x: None)
print(results)
```

### 5. Register Plugin

Plugins are automatically discovered if placed in:
- `kiss/plugins/` subdirectories
- `~/.kiss/plugins/` directory

## API Integration

### HTTP Requests

Use the built-in `_make_request()` method for HTTP calls:

```python
# GET request
response = await self._make_request(
    "https://api.example.com/endpoint",
    method="GET",
    params={"param": "value"}
)

# POST request
response = await self._make_request(
    "https://api.example.com/endpoint",
    method="POST",
    json_data={"key": "value"}
)

# With custom headers
response = await self._make_request(
    "https://api.example.com/endpoint",
    headers={"Authorization": f"Bearer {api_key}"}
)
```

### API Key Management

```python
# Get API key
api_key = self.get_api_key("api_key_name")

# Check if configured
if self.is_configured():
    # Proceed with API calls
else:
    # Return configuration error
    return [self._create_result(
        "Configuration",
        "API key not configured",
        threat_level="MEDIUM"
    )]
```

### Rate Limiting

Rate limiting is automatically applied based on your metadata:

```python
# Custom rate limiting (optional)
async def _rate_limit(self):
    # Custom logic if needed
    await super()._rate_limit()
```

## Error Handling

### Best Practices

1. **Never let exceptions escape**: Catch all exceptions
2. **Provide meaningful error messages**: Help users understand issues
3. **Use appropriate threat levels**: LOW, MEDIUM, HIGH, CRITICAL
4. **Graceful degradation**: Continue with partial results when possible

### Error Handling Pattern

```python
async def scan_async(self, target: str, scan_type: str, progress_callback: Callable[[float], None]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    
    try:
        # Main plugin logic
        response = await self._make_request(url)
        
        if response is None:
            results.append(self._create_result(
                "API Error",
                "Service unavailable",
                threat_level="MEDIUM"
            ))
        elif response.status != 200:
            results.append(self._create_result(
                "API Error",
                f"HTTP {response.status}: {response.reason}",
                threat_level="HIGH"
            ))
        else:
            # Process successful response
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
            "Plugin Error",
            f"Unexpected error: {str(e)}",
            threat_level="HIGH"
        ))
    
    return results
```

## Testing

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock, patch
from kiss.plugins.my_category.my_plugin import MyPlugin

@pytest.mark.asyncio
async def test_my_plugin():
    config = get_config()
    plugin = MyPlugin(config)
    
    # Mock API response
    with patch.object(plugin, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value.status = 200
        mock_request.return_value.json = AsyncMock(return_value={"result": "test"})
        
        results = await plugin.scan_async("test@example.com", "EMAIL", lambda x: None)
        
        assert len(results) > 0
        assert any(r["label"] == "Analysis Result" for r in results)
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_plugin_with_real_api():
    config = get_config()
    plugin = MyPlugin(config)
    
    if plugin.is_configured():
        results = await plugin.scan_async("test@example.com", "EMAIL", lambda x: None)
        assert len(results) > 0
    else:
        pytest.skip("API key not configured")
```

## Deployment

### Plugin Distribution

1. **Core Plugins**: Include in main KISS repository
2. **Community Plugins**: Submit via pull request
3. **Private Plugins**: Place in `~/.kiss/plugins/`

### Version Management

```python
# Update version in metadata
version="1.2.3"

# Follow semantic versioning
# MAJOR.MINOR.PATCH
# 1.0.0 - Initial release
# 1.1.0 - Add feature
# 1.1.1 - Bug fix
# 2.0.0 - Breaking change
```

### Documentation

1. **Inline Documentation**: Docstrings for all methods
2. **README**: Plugin-specific documentation
3. **Examples**: Usage examples and sample outputs
4. **API Documentation**: External API details

## Examples

### Email Intelligence Plugin

See `kiss/plugins/templates/email_intelligence_template.py` for a complete example.

### Phone Intelligence Plugin

```python
class PhoneIntelligencePlugin(AsyncBasePlugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="phone_intelligence",
            display_name="Phone Intelligence",
            description="Advanced phone number analysis",
            version="1.0.0",
            category="Phone Intelligence",
            supported_scan_types=["PHONE"],
            api_key_requirements=[
                APIKeyRequirement(
                    key_name="phone_api",
                    env_var="KISS_PHONE_API_KEY",
                    display_name="Phone API Key",
                    description="Required for phone lookup",
                    is_required=True
                )
            ],
            rate_limit=100,
            timeout=15,
        )
    
    async def scan_async(self, target: str, scan_type: str, progress_callback: Callable[[float], None]) -> List[Dict[str, Any]]:
        results = []
        
        try:
            # Phone validation
            import phonenumbers
            parsed_number = phonenumbers.parse(target, None)
            
            if phonenumbers.is_valid_number(parsed_number):
                results.append(self._create_result(
                    "Validation",
                    "Valid phone number",
                    source="Phone Parser"
                ))
                
                # API lookup
                if self.is_configured():
                    api_results = await self._lookup_phone(parsed_number)
                    results.extend(api_results)
            
        except Exception as e:
            results.append(self._create_result(
                "Error",
                f"Phone analysis failed: {str(e)}",
                threat_level="HIGH"
            ))
        
        return results
    
    async def _lookup_phone(self, parsed_number) -> List[Dict[str, Any]]:
        # API integration logic
        pass
```

### Username Enumeration Plugin

```python
class UsernameEnumerationPlugin(AsyncBasePlugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="username_enumeration",
            display_name="Username Enumeration",
            description="Check username across multiple platforms",
            version="1.0.0",
            category="Username Intelligence",
            supported_scan_types=["USERNAME"],
            api_key_requirements=[],  # No API key required
            rate_limit=30,  # Be respectful to platforms
            timeout=10,
        )
    
    async def scan_async(self, target: str, scan_type: str, progress_callback: Callable[[float], None]) -> List[Dict[str, Any]]:
        results = []
        
        # Platform definitions
        platforms = [
            ("GitHub", "https://github.com/{}", "head_200"),
            ("Twitter", "https://twitter.com/{}", "head_200"),
            ("Instagram", "https://instagram.com/{}", "head_200"),
        ]
        
        # Check platforms concurrently
        tasks = []
        for platform_name, url_template, method in platforms:
            task = self._check_platform(target, platform_name, url_template)
            tasks.append(task)
        
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in platform_results:
            if isinstance(result, dict):
                results.append(result)
        
        return results
    
    async def _check_platform(self, username: str, platform_name: str, url_template: str) -> Dict[str, Any]:
        try:
            url = url_template.format(username)
            response = await self._make_request(url, method="HEAD")
            
            if response and response.status == 200:
                return self._create_result(
                    "Platform Found",
                    platform_name,
                    source="Platform Check"
                )
        except Exception:
            pass
        
        return {}
```

## Plugin Development Checklist

- [ ] Choose async or sync implementation
- [ ] Implement required methods (`get_metadata`, `scan_async`/`scan`)
- [ ] Add proper error handling
- [ ] Include progress callbacks
- [ ] Configure rate limiting
- [ ] Add API key requirements
- [ ] Write comprehensive tests
- [ ] Document plugin functionality
- [ ] Test with real APIs
- [ ] Validate plugin registration
- [ ] Check backward compatibility

## Support and Community

- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Contributions**: Submit Pull Requests for improvements
- **Documentation**: Help improve plugin development guides

## Advanced Topics

### Custom Rate Limiting

```python
async def _rate_limit(self):
    """Custom rate limiting for complex APIs."""
    if self.metadata.rate_limit <= 0:
        return
    
    # Custom logic for tiered rate limits
    if hasattr(self, '_request_count'):
        if self._request_count % 10 == 0:
            await asyncio.sleep(1.0)  # Pause every 10 requests
    
    await super()._rate_limit()
```

### Plugin Dependencies

```python
@classmethod
def get_metadata(cls) -> PluginMetadata:
    return PluginMetadata(
        # ... other metadata
        dependencies=["base_email_plugin"],  # Requires this plugin
    )
```

### Custom Result Processing

```python
def _create_enhanced_result(self, label: str, value: str, **kwargs) -> Dict[str, Any]:
    """Create enhanced result with custom metadata."""
    result = self._create_result(label, value, **kwargs)
    
    # Add custom metadata
    result["metadata"] = {
        "plugin_version": self.metadata.version,
        "scan_timestamp": time.time(),
        "confidence": kwargs.get("confidence", 1.0),
    }
    
    return result
```

This comprehensive guide should help you create robust, efficient plugins for the KISS OSINT toolkit. Remember to follow best practices for async programming, error handling, and API integration.