"""KISS Query Parser.

Strict query parser with validation for structured queries.
Supports field:"value" format with comprehensive validation.
"""

import re
import ipaddress
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

from kiss.constants import ScanType


class QueryFieldType(Enum):
    """Supported query field types."""

    EMAIL = "email"
    PHONE = "phone"
    IP = "ip"
    USERNAME = "username"
    ADDRESS = "address"
    HASH = "hash"
    NAME = "name"
    LOCATION = "location"
    SSID = "ssid"
    BSSID = "bssid"
    DOMAIN = "domain"
    URL = "url"


@dataclass
class QueryFilter:
    """Represents a single query filter."""

    field: QueryFieldType
    value: str
    is_quoted: bool = False


@dataclass
class ParsedQuery:
    """Represents a parsed structured query."""

    primary_target: str
    primary_type: Optional[QueryFieldType] = None
    filters: List[QueryFilter] = None
    raw_query: str = ""
    confidence: float = 1.0


class QueryValidationError(Exception):
    """Raised when query validation fails."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(message)
        self.suggestion = suggestion


class QueryParser:
    """Strict query parser with comprehensive validation.

    Supported syntax:
    - Simple targets: user@example.com, +1234567890, 192.168.1.1
    - Field syntax: email:"user@domain.com"
    - Strict validation: fails fast on invalid input
    - Multiple filters: name:"John Doe" location:"New York"

    Examples:
        email:"user@domain.com"
        phone:"+1234567890"
        name:"John Doe" location:"New York, US"
        ip:"192.168.1.1"
        username:"johndoe"
        address:"123 Main St, City, Country"
        hash:"5d41402abc4b2a76b9719d911017c592"
        ssid:"MyWiFi"
        bssid:"00:11:22:33:44:55"
    """

    # Strict regex patterns
    FIELD_QUOTED_PATTERN = re.compile(r'^([a-zA-Z_]+):"([^"]*)"$')
    FIELD_SIMPLE_PATTERN = re.compile(r'^([a-zA-Z_]+):([^"\s]+)$')

    # Validation patterns
    EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{10,}$")
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")
    BSSID_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{32,128}$")
    DOMAIN_PATTERN = re.compile(
        r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9])*$"
    )
    URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

    SUPPORTED_FIELDS = {
        "email": QueryFieldType.EMAIL,
        "phone": QueryFieldType.PHONE,
        "ip": QueryFieldType.IP,
        "username": QueryFieldType.USERNAME,
        "address": QueryFieldType.ADDRESS,
        "hash": QueryFieldType.HASH,
        "name": QueryFieldType.NAME,
        "location": QueryFieldType.LOCATION,
        "ssid": QueryFieldType.SSID,
        "bssid": QueryFieldType.BSSID,
        "domain": QueryFieldType.DOMAIN,
        "url": QueryFieldType.URL,
    }

    @classmethod
    def parse_query(cls, query: str) -> ParsedQuery:
        """Parse query with strict validation.

        Args:
            query: Raw query string

        Returns:
            ParsedQuery object

        Raises:
            QueryValidationError: If query is invalid
        """
        query = query.strip()

        if not query:
            raise QueryValidationError(
                "Empty query not allowed", 'Example: email:"user@domain.com"'
            )

        # Split query into tokens (handling quoted values)
        tokens = cls._tokenize_query(query)

        if not tokens:
            raise QueryValidationError(
                "No valid query tokens found", "Example: phone:+1234567890"
            )

        primary_target = None
        primary_type = None
        filters = []

        for i, token in enumerate(tokens):
            if ":" in token:
                # Field:value format
                try:
                    field, value = cls._parse_field_value(token)
                except QueryValidationError as e:
                    raise QueryValidationError(
                        f"Invalid token {i + 1}: {e}",
                        f'Use format: field:"value" or field:value',
                    )

                if field not in cls.SUPPORTED_FIELDS:
                    raise QueryValidationError(
                        f"Unsupported field: {field}",
                        f"Supported fields: {', '.join(cls.SUPPORTED_FIELDS.keys())}",
                    )

                field_type = cls.SUPPORTED_FIELDS[field]
                filters.append(QueryFilter(field_type, value, '"' in token))

                # First field token becomes primary target
                if primary_target is None:
                    primary_target = value
                    primary_type = field_type
            else:
                # Simple target (no field specified)
                if primary_target is not None:
                    raise QueryValidationError(
                        "Multiple simple targets not allowed",
                        "Use field:value format for all targets",
                    )
                primary_target = token
                primary_type = cls._detect_target_type(token)

        if primary_target is None:
            raise QueryValidationError(
                "No valid target found in query", 'Example: email:"user@domain.com"'
            )

        # Validate primary target
        if primary_type:
            cls._validate_target(primary_target, primary_type)

        # Validate all filters
        for i, filter_item in enumerate(filters):
            try:
                cls._validate_target(filter_item.value, filter_item.field)
            except QueryValidationError as e:
                raise QueryValidationError(
                    f"Invalid value in filter {i + 1}: {e}",
                    f"Check value format for {filter_item.field.value} field",
                )

        return ParsedQuery(
            primary_target=primary_target,
            primary_type=primary_type,
            filters=filters,
            raw_query=query,
        )

    @classmethod
    def _tokenize_query(cls, query: str) -> List[str]:
        """Tokenize query string, handling quoted values properly."""
        tokens = []
        current_token = ""
        in_quotes = False
        quote_char = None

        for char in query:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                current_token += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current_token += char
            elif char.isspace() and not in_quotes:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char

        if current_token:
            tokens.append(current_token)

        # Validate quote pairing
        if in_quotes:
            raise QueryValidationError(
                "Unclosed quotes in query", "Ensure all quoted values are closed"
            )

        return tokens

    @classmethod
    def _parse_field_value(cls, token: str) -> Tuple[str, str]:
        """Parse field:value token with validation."""
        if '"' in token:
            # Quoted value: field:"value"
            match = cls.FIELD_QUOTED_PATTERN.match(token)
            if not match:
                raise QueryValidationError(
                    f"Invalid quoted field format: {token}", 'Use format: field:"value"'
                )
            return match.group(1), match.group(2)
        else:
            # Simple value: field:value
            match = cls.FIELD_SIMPLE_PATTERN.match(token)
            if not match:
                raise QueryValidationError(
                    f"Invalid field format: {token}",
                    'Use format: field:value or field:"value"',
                )
            return match.group(1), match.group(2)

    @classmethod
    def _validate_target(cls, target: str, field_type: QueryFieldType):
        """Strict validation for each target type."""
        if field_type == QueryFieldType.EMAIL:
            if not cls.EMAIL_PATTERN.match(target):
                raise QueryValidationError(
                    f"Invalid email format: {target}", "Use format: user@domain.com"
                )

        elif field_type == QueryFieldType.PHONE:
            if not cls.PHONE_PATTERN.match(target):
                raise QueryValidationError(
                    f"Invalid phone format: {target}",
                    "Use format: +1234567890 or (123) 456-7890",
                )

        elif field_type == QueryFieldType.IP:
            try:
                ipaddress.ip_address(target)
            except ValueError:
                raise QueryValidationError(
                    f"Invalid IP address: {target}",
                    "Use format: 192.168.1.1 or 2001:db8::1",
                )

        elif field_type == QueryFieldType.USERNAME:
            if not cls.USERNAME_PATTERN.match(target):
                raise QueryValidationError(
                    f"Invalid username format: {target}",
                    "Username must be 3-30 chars, alphanumeric + _-",
                )

        elif field_type == QueryFieldType.HASH:
            if not cls.HASH_PATTERN.match(target):
                raise QueryValidationError(
                    f"Invalid hash format: {target}",
                    "Hash must be 32-128 hex characters",
                )

        elif field_type == QueryFieldType.BSSID:
            if not cls.BSSID_PATTERN.match(target):
                raise QueryValidationError(
                    f"Invalid BSSID format: {target}",
                    "Use format: 00:11:22:33:44:55 or 00-11-22-33-44-55",
                )

        elif field_type == QueryFieldType.DOMAIN:
            if not cls.DOMAIN_PATTERN.match(target):
                raise QueryValidationError(
                    f"Invalid domain format: {target}",
                    "Use format: example.com or sub.example.com",
                )

        elif field_type == QueryFieldType.URL:
            if not cls.URL_PATTERN.match(target):
                raise QueryValidationError(
                    f"Invalid URL format: {target}",
                    "Use format: https://example.com/path",
                )

        # NAME, LOCATION, SSID, ADDRESS are more flexible and require minimal validation
        elif field_type in [
            QueryFieldType.NAME,
            QueryFieldType.LOCATION,
            QueryFieldType.ADDRESS,
            QueryFieldType.SSID,
        ]:
            if len(target.strip()) < 1:
                raise QueryValidationError(
                    f"Empty value for field type: {field_type.value}",
                    f"Provide a valid {field_type.value}",
                )

    @classmethod
    def _detect_target_type(cls, target: str) -> Optional[QueryFieldType]:
        """Auto-detect target type for simple queries."""
        # Import existing detection logic
        from .detectors import detect_input_type

        detected_type = detect_input_type(target)
        if detected_type:
            return QueryFieldType(detected_type.lower())
        return None

    @classmethod
    def get_syntax_help(cls) -> str:
        """Get syntax help documentation."""
        return """
KISS Query Syntax Help

BASIC FORMATS:
  Simple Target: user@example.com
  Field Target:  email:"user@domain.com"
  
FIELD SYNTAX:
  field:"quoted value"    - For values with spaces
  field:simple_value      - For single words/numbers
  
SUPPORTED FIELDS:
  email:     user@domain.com
  phone:     +1234567890
  ip:        192.168.1.1
  username:  johndoe
  address:   "123 Main St, City, Country"
  hash:      5d41402abc4b2a76b9719d911017c592
  name:      "John Doe"
  location:  "New York, US"
  ssid:      MyWiFi
  bssid:     00:11:22:33:44:55
  domain:    example.com
  url:       https://example.com

MULTIPLE FILTERS:
  name:"John Doe" location:"New York, US"
  email:"user@domain.com" domain:"gmail.com"

EXAMPLES:
  email:"user@domain.com"
  phone:"+1234567890"
  name:"John Doe" location:"Boston, MA"
  ip:"192.168.1.1" country:"US"
  username:"johndoe" platform:"twitter"
  hash:"5d41402abc4b2a76b9719d911017c592"
  
VALIDATION:
  Strict validation applies to all fields
  Invalid queries fail fast with helpful error messages
  All fields except name/location/address/ssid require specific formats
"""

    @classmethod
    def validate_query_structure(cls, query: str) -> Tuple[bool, Optional[str]]:
        """Quick validation of query structure without full parsing."""
        try:
            cls.parse_query(query)
            return True, None
        except QueryValidationError as e:
            return False, str(e)


# Utility functions for TUI integration
def is_structured_query(query: str) -> bool:
    """Check if query uses structured field syntax."""
    return ":" in query and any(
        field in query.lower() for field in QueryParser.SUPPORTED_FIELDS.keys()
    )


def get_query_suggestions(partial_query: str) -> List[str]:
    """Get suggestions for partial query input."""
    suggestions = []

    # Field name suggestions
    if ":" not in partial_query:
        for field in QueryParser.SUPPORTED_FIELDS.keys():
            suggestions.append(f"{field}:")

    return suggestions


def format_query_example(field_type: QueryFieldType) -> str:
    """Get example query for a field type."""
    examples = {
        QueryFieldType.EMAIL: 'email:"user@domain.com"',
        QueryFieldType.PHONE: 'phone:"+1234567890"',
        QueryFieldType.IP: 'ip:"192.168.1.1"',
        QueryFieldType.USERNAME: 'username:"johndoe"',
        QueryFieldType.ADDRESS: 'address:"123 Main St, City, Country"',
        QueryFieldType.HASH: 'hash:"5d41402abc4b2a76b9719d911017c592"',
        QueryFieldType.NAME: 'name:"John Doe"',
        QueryFieldType.LOCATION: 'location:"New York, US"',
        QueryFieldType.SSID: 'ssid:"MyWiFi"',
        QueryFieldType.BSSID: 'bssid:"00:11:22:33:44:55"',
        QueryFieldType.DOMAIN: 'domain:"example.com"',
        QueryFieldType.URL: 'url:"https://example.com"',
    }

    return examples.get(field_type, "")


def get_all_field_descriptions() -> Dict[str, str]:
    """Get descriptions for all supported fields."""
    return {
        "email": "Email address for breach detection and verification",
        "phone": "Phone number for carrier and location analysis",
        "ip": "IP address for geolocation and network intelligence",
        "username": "Username for platform enumeration",
        "address": "Physical address for geocoding and validation",
        "hash": "Password hash for breach database lookup",
        "name": "Person name for identity investigation",
        "location": "Geographic location for filtering",
        "ssid": "WiFi network name for geolocation",
        "bssid": "WiFi MAC address for network analysis",
        "domain": "Domain name for DNS and web analysis",
        "url": "URL for content and hosting analysis",
    }
