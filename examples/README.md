# Examples README

This directory contains demonstration scripts and examples for KISS OSINT toolkit.

## Available Examples

### Phone Analysis Demo
```bash
python examples/phone_analysis_demo.py
```
Demonstrates enhanced phone number analysis including:
- International format validation
- Carrier detection
- Geographic lookup
- Line type analysis
- Threat assessment

### Comprehensive Demo
```bash
python examples/comprehensive_demo.py
```
Full-featured demonstration showcasing:
- All input types
- Multiple plugin integrations
- Advanced filtering
- Export capabilities

### TUI Demo
```bash
python examples/tui_demo.py
```
Terminal User Interface demonstration:
- Modern curses-based interface
- Real-time progress updates
- Interactive scanning
- Color-coded results

### Modern Demo
```bash
python examples/modern_demo.py
```
Modern architecture demonstration:
- Async plugin usage
- Concurrent scanning
- Error handling
- Resource management

### Enhanced Demo
```bash
python examples/enhanced_demo.py
```
Enhanced features demonstration:
- Advanced query syntax
- Multi-modal analysis
- Intelligent filtering
- Comprehensive reporting

### Advanced Demo
```bash
python examples/advanced_demo.py
```
Advanced capabilities demonstration:
- Custom plugin integration
- Complex workflows
- Performance optimization
- Security features

### Legacy Demo
```bash
python examples/legacy_demo.py
```
Historical reference showing:
- Original implementation
- Architecture evolution
- Feature progression
- Migration examples

## Usage Patterns

### Basic Scanning
```python
from kiss import get_engine

engine = get_engine()
result = engine.scan("user@example.com")

for row in result.info_rows:
    print(f"{row.label}: {row.value}")
```

### Advanced Scanning
```python
from kiss.async_engine import get_async_engine
import asyncio

async def scan_example():
    engine = get_async_engine()
    result = await engine.scan_async("user@example.com")
    return result

# Run async scan
result = asyncio.run(scan_example())
```

### Plugin Development
See the templates in `../kiss/plugins/templates/` for plugin development examples:
- `email_intelligence_template.py` - Email analysis plugin
- `phone_intelligence_template.py` - Phone intelligence plugin

## Configuration

Most examples support environment variables for configuration:

```bash
export KISS_HIBP_API_KEY="your_api_key"
export KISS_IPINFO_API_KEY="your_api_key"
export KISS_PHONE_API_KEY="your_api_key"
```

Or create a configuration file:
```bash
cp config.example.json ~/.kiss/config.json
# Edit with your API keys
```

## Integration Examples

### Batch Processing
```python
targets = ["user1@example.com", "user2@example.com", "user3@example.com"]
results = []

for target in targets:
    result = engine.scan(target)
    results.append(result)
```

### Custom Workflows
```python
# Email → Phone → Username analysis
email_result = engine.scan("user@example.com")
if phone_found := get_phone_from_result(email_result):
    phone_result = engine.scan(phone_found)
    if username_found := get_username_from_result(phone_result):
        username_result = engine.scan(username_found)
```

## Error Handling

All examples include comprehensive error handling:

```python
try:
    result = engine.scan(target)
    if result.status == "completed":
        print("Scan successful")
    else:
        print(f"Scan failed: {result.error_message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Testing

Some examples include performance testing capabilities:

```bash
# Run with timing
python examples/performance_demo.py --timing

# Run with concurrency
python examples/performance_demo.py --workers 5
```

## Contributing

To add new examples:

1. Create descriptive filename
2. Include comprehensive documentation
3. Add error handling
4. Test with all supported Python versions
5. Update this README

## Support

For questions about examples:
- Check [Plugin Development Guide](../docs/PLUGIN_DEVELOPMENT.md)
- Review [Main Documentation](../README.md)
- Open an [Issue](../../issues) with "example" label

## Security Notes

When running examples:
- Never commit API keys
- Use environment variables for sensitive data
- Review example code before running
- Test with non-production data first