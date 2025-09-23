# app/services/storage_service.py
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

class StorageService:
    """Storage Service - Handles all data persistence operations"""

    def __init__(self):
        # Create data directory structure
        self.base_dir = Path("data")
        self.json_dir = self.base_dir / "json"
        self.cache_dir = self.base_dir / "cache"
        self.backup_dir = self.base_dir / "backups"

        # Create directories
        for directory in [self.base_dir, self.json_dir, self.cache_dir, self.backup_dir]:
            directory.mkdir(exist_ok=True)

        # File configurations
        self.files = {
            "current_ipos": "current_ipos.json",
            "upcoming_ipos": "upcoming_ipos.json",
            "market_status": "market_status.json",
        }

        # Cache settings (in seconds)
        self.cache_duration = {
            "current_ipos": 300,    # 5 minutes
            "upcoming_ipos": 3600,  # 1 hour
            "market_status": 300,   # 5 minutes
        }

        # Thread lock for file operations
        self.file_lock = threading.Lock()

        logger.info("Storage Service: Initialized with directory structure")

    def save_data(self, data_type: str, data: List[Dict], source: str = "unknown") -> bool:
        """Save data to JSON file with metadata"""
        
        if data_type not in self.files and not data_type.startswith("subscription_"):
            logger.error(f"Storage Service: Unknown data type - {data_type}")
            return False

        try:
            with self.file_lock:
                # Prepare data package with metadata
                data_package = {
                    "metadata": {
                        "data_type": data_type,
                        "source": source,
                        "timestamp": datetime.now().isoformat(),
                        "count": len(data) if isinstance(data, list) else 1,
                        "version": self._get_next_version(data_type),
                    },
                    "data": data,
                }

                # Get file path
                if data_type in self.files:
                    file_path = self.json_dir / self.files[data_type]
                else:
                    # Dynamic file for subscription data
                    file_path = self.json_dir / f"{data_type}.json"

                # Backup existing file if it exists
                if file_path.exists():
                    self._backup_file(file_path, data_type)

                # Write new data
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data_package, f, indent=2, ensure_ascii=False)

                logger.info(f"Storage Service: Saved {data_type} - {len(data) if isinstance(data, list) else 1} records")
                return True

        except Exception as e:
            logger.error(f"Storage Service: Failed to save {data_type} - {e}")
            return False

    def load_data(self, data_type: str, max_age_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Load data from JSON file"""
        
        try:
            # Get file path
            if data_type in self.files:
                file_path = self.json_dir / self.files[data_type]
            else:
                # Dynamic file for subscription data
                file_path = self.json_dir / f"{data_type}.json"

            if not file_path.exists():
                logger.warning(f"Storage Service: File not found - {data_type}")
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data_package = json.load(f)

            # Check data age if specified
            if max_age_seconds:
                timestamp = datetime.fromisoformat(data_package["metadata"]["timestamp"])
                age = (datetime.now() - timestamp).total_seconds()

                if age > max_age_seconds:
                    logger.info(f"Storage Service: Data expired - {data_type} (age: {age:.0f}s)")
                    return None

            logger.info(f"Storage Service: Loaded {data_type} - {data_package['metadata']['count']} records")
            return data_package

        except Exception as e:
            logger.error(f"Storage Service: Failed to load {data_type} - {e}")
            return None

    def get_cached_data(self, data_type: str, use_default_cache_duration: bool = True) -> Optional[Dict[str, Any]]:
        """Get cached data with automatic expiry check"""
        
        if use_default_cache_duration:
            cache_duration = self.cache_duration.get(data_type, 300)  # Default 5 minutes
            return self.load_data(data_type, cache_duration)
        else:
            return self.load_data(data_type)

    def get_data_age(self, data_type: str) -> Optional[int]:
        """Get age of data in seconds"""
        try:
            # Get file path
            if data_type in self.files:
                file_path = self.json_dir / self.files[data_type]
            else:
                file_path = self.json_dir / f"{data_type}.json"

            if not file_path.exists():
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                data_package = json.load(f)

            timestamp = datetime.fromisoformat(data_package["metadata"]["timestamp"])
            age = (datetime.now() - timestamp).total_seconds()
            return int(age)

        except Exception as e:
            logger.error(f"Storage Service: Failed to get age for {data_type} - {e}")
            return None

    def is_data_fresh(self, data_type: str, freshness_seconds: int = None) -> bool:
        """Check if data is fresh (within specified time)"""
        if freshness_seconds is None:
            freshness_seconds = self.cache_duration.get(data_type, 300)

        data_package = self.load_data(data_type, freshness_seconds)
        return data_package is not None

    def list_all_data_files(self) -> Dict[str, Dict[str, Any]]:
        """List all data files with their metadata"""
        file_info = {}

        # Check configured files
        for data_type, filename in self.files.items():
            file_path = self.json_dir / filename
            file_info[data_type] = self._get_file_info(file_path, data_type)

        # Check for subscription files
        for subscription_file in self.json_dir.glob("subscription_*.json"):
            data_type = subscription_file.stem
            file_info[data_type] = self._get_file_info(subscription_file, data_type)

        return file_info

    def _get_file_info(self, file_path: Path, data_type: str) -> Dict[str, Any]:
        """Get information about a specific file"""
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data_package = json.load(f)

                return {
                    "exists": True,
                    "metadata": data_package["metadata"],
                    "file_size_bytes": file_path.stat().st_size,
                    "file_size_readable": self._format_bytes(file_path.stat().st_size),
                    "age_seconds": self.get_data_age(data_type),
                    "is_fresh": self.is_data_fresh(data_type),
                }
            except Exception as e:
                return {
                    "exists": True,
                    "error": str(e),
                    "file_size_bytes": file_path.stat().st_size,
                }
        else:
            return {"exists": False}

    def clean_expired_data(self) -> Dict[str, int]:
        """Clean expired data files and old backups"""
        cleanup_stats = {
            "expired_files_cleaned": 0,
            "old_backups_cleaned": 0,
            "errors": 0,
        }

        try:
            # Clean expired cache files for configured types
            for data_type in self.files.keys():
                if not self.is_data_fresh(data_type):
                    file_path = self.json_dir / self.files[data_type]
                    if file_path.exists():
                        try:
                            file_path.unlink()
                            cleanup_stats["expired_files_cleaned"] += 1
                            logger.info(f"Storage Service: Cleaned expired {data_type}")
                        except Exception as e:
                            logger.error(f"Storage Service: Failed to clean {data_type} - {e}")
                            cleanup_stats["errors"] += 1

            # Clean old backups (older than 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)
            for backup_file in self.backup_dir.glob("*.json"):
                try:
                    if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                        backup_file.unlink()
                        cleanup_stats["old_backups_cleaned"] += 1
                        logger.info(f"Storage Service: Cleaned old backup {backup_file.name}")
                except Exception as e:
                    logger.error(f"Storage Service: Failed to clean backup {backup_file} - {e}")
                    cleanup_stats["errors"] += 1

        except Exception as e:
            logger.error(f"Storage Service: Cleanup operation failed - {e}")
            cleanup_stats["errors"] += 1

        return cleanup_stats

    def _backup_file(self, file_path: Path, data_type: str):
        """Create backup of existing file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{data_type}_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_name

            # Copy existing file to backup
            import shutil
            shutil.copy2(file_path, backup_path)

            logger.info(f"Storage Service: Backup created - {backup_name}")

        except Exception as e:
            logger.warning(f"Storage Service: Failed to create backup for {data_type} - {e}")

    def _get_next_version(self, data_type: str) -> int:
        """Get next version number for data type"""
        try:
            if data_type in self.files:
                file_path = self.json_dir / self.files[data_type]
            else:
                file_path = self.json_dir / f"{data_type}.json"

            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data_package = json.load(f)
                current_version = data_package.get("metadata", {}).get("version", 0)
                return current_version + 1

            return 1

        except Exception:
            return 1

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            "base_directory": str(self.base_dir),
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_readable": "0 B",
            "data_types": {},
            "backup_count": 0,
            "cache_settings": self.cache_duration,
        }

        try:
            # Count main data files
            for data_type, filename in self.files.items():
                file_path = self.json_dir / filename
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    stats["total_files"] += 1
                    stats["total_size_bytes"] += file_size

                    stats["data_types"][data_type] = {
                        "file_size_bytes": file_size,
                        "file_size_readable": self._format_bytes(file_size),
                        "age_seconds": self.get_data_age(data_type),
                        "is_fresh": self.is_data_fresh(data_type),
                    }

            # Count subscription files
            for subscription_file in self.json_dir.glob("subscription_*.json"):
                file_size = subscription_file.stat().st_size
                stats["total_files"] += 1
                stats["total_size_bytes"] += file_size

            # Count backup files
            stats["backup_count"] = len(list(self.backup_dir.glob("*.json")))

            # Convert total bytes to readable format
            stats["total_size_readable"] = self._format_bytes(stats["total_size_bytes"])

        except Exception as e:
            logger.error(f"Storage Service: Failed to get storage stats - {e}")
            stats["error"] = str(e)

        return stats

    def _format_bytes(self, bytes_size: int) -> str:
        """Format bytes to readable string"""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on storage system"""
        health_info = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "directories_accessible": True,
            "file_permissions_ok": True,
            "storage_space_ok": True,
            "issues": [],
        }

        try:
            # Check directory access
            for directory in [self.base_dir, self.json_dir, self.cache_dir, self.backup_dir]:
                if not directory.exists() or not os.access(directory, os.R_OK | os.W_OK):
                    health_info["directories_accessible"] = False
                    health_info["issues"].append(f"Directory access issue: {directory}")

            # Check file permissions for existing files
            for data_type, filename in self.files.items():
                file_path = self.json_dir / filename
                if file_path.exists() and not os.access(file_path, os.R_OK | os.W_OK):
                    health_info["file_permissions_ok"] = False
                    health_info["issues"].append(f"File permission issue: {filename}")

            # Check storage space (basic test)
            try:
                test_file = self.json_dir / "health_check_test.tmp"
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                health_info["storage_space_ok"] = False
                health_info["issues"].append(f"Storage space issue: {e}")

            # Overall status
            if health_info["issues"]:
                health_info["status"] = "issues_detected"

        except Exception as e:
            health_info["status"] = "error"
            health_info["issues"].append(f"Health check failed: {e}")

        return health_info

    def register_data_type(self, data_type: str, filename: str, cache_duration: int = 300) -> bool:
        """Register a new data type dynamically (for subscription files)"""
        try:
            if data_type in self.files:
                logger.warning(f"Storage Service: Data type {data_type} already exists")
                return False

            self.files[data_type] = filename
            self.cache_duration[data_type] = cache_duration

            logger.info(f"Storage Service: Registered {data_type} -> {filename} (cache: {cache_duration}s)")
            return True

        except Exception as e:
            logger.error(f"Storage Service: Failed to register {data_type} - {e}")
            return False

    def get_registered_types(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered data types with their settings"""
        return {
            data_type: {
                "filename": filename,
                "cache_duration": self.cache_duration.get(data_type, 300),
                "file_exists": (self.json_dir / filename).exists(),
            }
            for data_type, filename in self.files.items()
        }

    def export_all_data(self, export_path: str = None) -> str:
        """Export all data to a single JSON file"""
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.base_dir / f"full_export_{timestamp}.json"

        try:
            export_data = {
                "export_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "total_data_types": len(self.files),
                },
                "data": {},
            }

            for data_type in self.files.keys():
                data_package = self.load_data(data_type)
                if data_package:
                    export_data["data"][data_type] = data_package

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Storage Service: Data exported to {export_path}")
            return str(export_path)

        except Exception as e:
            logger.error(f"Storage Service: Export failed - {e}")
            raise

    def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Storage Service: Cleaned up")
        except Exception as e:
            logger.warning(f"Storage Service: Cleanup warning - {e}")

# Create service instance
storage_service = StorageService()