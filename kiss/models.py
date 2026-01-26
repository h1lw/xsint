"""XSINT Data Models.

Defines data structures and models used throughout the XSINT application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum

from kiss.constants import ScanType, ScanStatus, ThreatLevel


@dataclass
class InfoRow:
    """Represents a single row of information in scan results."""

    label: str
    value: str
    threat_level: Optional[ThreatLevel] = None
    source: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanResult:
    """Represents the result of a single scan operation."""

    scan_type: ScanType
    target: str
    status: ScanStatus
    info_rows: List[InfoRow] = field(default_factory=list)
    error_message: Optional[str] = None
    scan_duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_info(
        self,
        label: str,
        value: str,
        threat_level: Optional[ThreatLevel] = None,
        source: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an information row to the scan result."""
        self.info_rows.append(
            InfoRow(
                label=label,
                value=value,
                threat_level=threat_level,
                source=source,
                confidence=confidence,
                metadata=metadata or {},
            )
        )

    def get_high_threat_info(self) -> List[InfoRow]:
        """Get all information rows with high or critical threat level."""
        return [
            row
            for row in self.info_rows
            if row.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        ]

    def get_info_by_source(self, source: str) -> List[InfoRow]:
        """Get all information rows from a specific source."""
        return [row for row in self.info_rows if row.source == source]

    def to_dict(self) -> Dict[str, Any]:
        """Convert scan result to dictionary format."""
        return {
            "scan_type": self.scan_type.value,
            "target": self.target,
            "status": self.status.value,
            "info_rows": [
                {
                    "label": row.label,
                    "value": row.value,
                    "threat_level": row.threat_level.value
                    if row.threat_level
                    else None,
                    "source": row.source,
                    "confidence": row.confidence,
                    "metadata": row.metadata,
                }
                for row in self.info_rows
            ],
            "error_message": self.error_message,
            "scan_duration": self.scan_duration,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ScanReport:
    """Represents a comprehensive scan report with multiple results."""

    target: str
    scan_results: List[ScanResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def add_result(self, result: ScanResult) -> None:
        """Add a scan result to the report."""
        self.scan_results.append(result)
        self._update_summary()

    def get_results_by_type(self, scan_type: ScanType) -> List[ScanResult]:
        """Get all results of a specific scan type."""
        return [result for result in self.scan_results if result.scan_type == scan_type]

    def get_all_high_threats(self) -> List[InfoRow]:
        """Get all high threat information from all scan results."""
        high_threats = []
        for result in self.scan_results:
            high_threats.extend(result.get_high_threat_info())
        return high_threats

    def _update_summary(self) -> None:
        """Update the report summary based on current results."""
        total_scans = len(self.scan_results)
        successful_scans = len(
            [r for r in self.scan_results if r.status == ScanStatus.COMPLETED]
        )
        total_info_rows = sum(len(r.info_rows) for r in self.scan_results)
        high_threat_count = len(self.get_all_high_threats())

        self.summary = {
            "total_scans": total_scans,
            "successful_scans": successful_scans,
            "failed_scans": total_scans - successful_scans,
            "total_info_rows": total_info_rows,
            "high_threat_count": high_threat_count,
            "scan_types": list(set(r.scan_type.value for r in self.scan_results)),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert scan report to dictionary format."""
        return {
            "target": self.target,
            "created_at": self.created_at.isoformat(),
            "scan_results": [result.to_dict() for result in self.scan_results],
            "summary": self.summary,
            "recommendations": self.recommendations,
        }


@dataclass
class APIKey:
    """Represents an API key configuration."""

    name: str
    key: str
    service: str
    rate_limit: int = 30  # requests per minute
    last_used: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceConfig:
    """Configuration for external services."""

    name: str
    base_url: str
    api_key: Optional[APIKey] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 30
    headers: Dict[str, str] = field(default_factory=dict)
    is_enabled: bool = True


@dataclass
class UserSession:
    """Represents a user session."""

    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    scan_history: List[ScanResult] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()

    def add_to_history(self, result: ScanResult) -> None:
        """Add a scan result to the session history."""
        self.scan_history.append(result)
        self.update_activity()


@dataclass
class CacheEntry:
    """Represents a cache entry for scan results."""

    key: str
    data: Union[ScanResult, Dict[str, Any]]
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def increment_hit(self) -> None:
        """Increment the hit count for this cache entry."""
        self.hit_count += 1


@dataclass
class ExportConfig:
    """Configuration for exporting scan results."""

    format: str  # json, csv, xml, etc.
    filename: Optional[str] = None
    include_metadata: bool = True
    include_summary: bool = True
    filter_by_threat: Optional[ThreatLevel] = None
    custom_fields: List[str] = field(default_factory=list)

    def should_include_row(self, row: InfoRow) -> bool:
        """Determine if an info row should be included based on filter."""
        if self.filter_by_threat is None:
            return True
        if row.threat_level is None:
            return False
        threat_levels = [
            ThreatLevel.LOW,
            ThreatLevel.MEDIUM,
            ThreatLevel.HIGH,
            ThreatLevel.CRITICAL,
        ]
        try:
            return threat_levels.index(row.threat_level) >= threat_levels.index(
                self.filter_by_threat
            )
        except (ValueError, IndexError):
            return False


@dataclass
class PluginConfig:
    """Configuration for plugins and extensions."""

    name: str
    version: str
    is_enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    def has_dependency(self, dependency: str) -> bool:
        """Check if the plugin has a specific dependency."""
        return dependency in self.dependencies


# Type aliases for common types
InfoDict = Dict[str, Any]
ResultDict = Dict[str, Any]
ConfigDict = Dict[str, Any]

# Common threat level assessments
THREAT_ASSESSMENTS = {
    "breached": ThreatLevel.HIGH,
    "compromised": ThreatLevel.CRITICAL,
    "vulnerable": ThreatLevel.MEDIUM,
    "suspicious": ThreatLevel.LOW,
    "safe": None,
}

# Confidence levels
CONFIDENCE_LEVELS = {
    "high": 0.9,
    "medium": 0.7,
    "low": 0.5,
    "very_low": 0.3,
}
