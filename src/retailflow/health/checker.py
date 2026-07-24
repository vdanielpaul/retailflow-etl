"""Pre-flight application health checks for RetailFlow ETL."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from retailflow.config.settings import Settings
from retailflow.database.connection import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Dataclass holding health check evaluation output."""

    is_healthy: bool
    checks: dict[str, bool]
    failures: list[str]


class HealthChecker:
    """Pre-flight environment and dependency health checker."""

    def __init__(
        self,
        settings: Settings,
        db_manager: DatabaseManager | None = None,
        min_free_disk_mb: int = 500,
    ) -> None:
        self.settings = settings
        self.db_manager = db_manager
        self.min_free_disk_mb = min_free_disk_mb

    def run_all_checks(self) -> HealthCheckResult:
        """Run all pre-flight health checks before starting batch processing.

        Returns:
            HealthCheckResult containing status boolean and detailed check details.
        """
        checks: dict[str, bool] = {}
        failures: list[str] = []

        # 1. Configuration Check
        checks["config_validity"] = self._check_config()
        if not checks["config_validity"]:
            failures.append("Configuration semantic check failed.")

        # 2. Directory Existence & Accessibility
        checks["directory_structure"] = self._check_directories()
        if not checks["directory_structure"]:
            failures.append("One or more required pipeline directories are missing or invalid.")

        # 3. Write Permissions Check
        checks["write_permissions"] = self._check_write_permissions()
        if not checks["write_permissions"]:
            failures.append("Pipeline log or data directories are not writable.")

        # 4. Free Disk Space Check
        checks["disk_space"] = self._check_disk_space()
        if not checks["disk_space"]:
            failures.append(f"Available disk space is below threshold of {self.min_free_disk_mb}MB.")

        # 5. Database Health Check (if DB manager injected)
        if self.db_manager is not None:
            checks["database_connectivity"] = self._check_database()
            if not checks["database_connectivity"]:
                failures.append("PostgreSQL database connection health check failed.")

        is_healthy = all(checks.values())
        return HealthCheckResult(is_healthy=is_healthy, checks=checks, failures=failures)

    def _check_config(self) -> bool:
        """Check configuration objects are properly instantiated."""
        return self.settings is not None and self.settings.pipeline.batch_size > 0

    def _check_directories(self) -> bool:
        """Verify input, raw, staging, archive, and log directories exist."""
        paths = self.settings.paths
        target_dirs = [
            paths.raw_dir,
            paths.staging_dir,
            paths.processed_dir,
            paths.archive_dir,
            paths.bad_records_dir,
            paths.log_dir,
        ]
        for d in target_dirs:
            p = Path(d)
            if not p.exists():
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create directory {p}: {e}")
                    return False
        return True

    def _check_write_permissions(self) -> bool:
        """Check write permission by creating and deleting a temporary test file."""
        log_dir = Path(self.settings.paths.log_dir)
        test_file = log_dir / ".write_test.tmp"
        try:
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Write permission check failed for {log_dir}: {e}")
            return False

    def _check_disk_space(self) -> bool:
        """Check available disk space on current partition."""
        try:
            total, used, free = shutil.disk_usage(self.settings.paths.raw_dir)
            free_mb = free / (1024 * 1024)
            return free_mb >= self.min_free_disk_mb
        except Exception as e:
            logger.warning(f"Disk space check warning: {e}")
            return True

    def _check_database(self) -> bool:
        """Check PostgreSQL database connectivity."""
        if self.db_manager is None:
            return True
        return self.db_manager.health_check()
