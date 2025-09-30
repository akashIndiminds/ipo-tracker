# app/utils/file_storage.py - FIXED directory structure

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class FileStorage:
    """Organized file storage - FIXED structure"""
    
    def __init__(self):
        self.base_dir = Path("data")
        self._create_directories()
    
    def _create_directories(self):
        """Create organized directory structure - NO extra folders"""
        dirs = [
            # NSE data
            "nse/current", 
            "nse/upcoming", 
            "nse/subscription",
            
            # Predictions only (no gmp/raw, gmp/predictions)
            "predictions/gmp",           # GMP predictions (renamed from gmp_current)
            "predictions/math",          # Math predictions
            "predictions/ai",            # AI predictions
            "predictions/final"          # Final combined predictions
        ]
        
        for dir_path in dirs:
            full_path = self.base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Directory ensured: {full_path}")
    
    def save_data(self, path: str, data: Dict, date_or_filename: str = None) -> bool:
        """
        Save data to organized path
        
        Args:
            path: Relative path like "nse/current" or "predictions/gmp"
            data: Data to save
            date_or_filename: Date (YYYY-MM-DD) or filename without extension
        
        Examples:
            save_data("nse/current", data, "2025-09-29")
            save_data("predictions/gmp", data, "2025-09-29")
            save_data("predictions/final_prediction/2025-09-29", data, "SYMBOL")
        """
        try:
            if not date_or_filename:
                date_or_filename = datetime.now().strftime("%Y-%m-%d")
            
            # Handle paths with date already in them (for final predictions)
            filepath = self.base_dir / path / f"{date_or_filename}.json"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            save_data = {
                'metadata': {
                    'path': path,
                    'filename': date_or_filename,
                    'timestamp': datetime.now().isoformat(),
                    'full_path': str(filepath)
                },
                'data': data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Save failed for {path}/{date_or_filename}: {e}")
            return False
    
    def load_data(self, path: str, date_or_filename: str = None) -> Optional[Dict]:
        """
        Load data from organized path
        
        Args:
            path: Relative path like "nse/current" or "predictions/gmp"
            date_or_filename: Date (YYYY-MM-DD) or filename without extension
        """
        try:
            if not date_or_filename:
                date_or_filename = datetime.now().strftime("%Y-%m-%d")
            
            filepath = self.base_dir / path / f"{date_or_filename}.json"
            
            if not filepath.exists():
                logger.warning(f"File not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"✅ Loaded: {filepath}")
            return data
                
        except Exception as e:
            logger.error(f"❌ Load failed for {path}/{date_or_filename}: {e}")
            return None
    
    def get_available_dates(self, path: str) -> List[str]:
        """Get list of available dates for a path"""
        try:
            dir_path = self.base_dir / path
            if not dir_path.exists():
                return []
            
            dates = []
            for file in dir_path.glob("*.json"):
                filename = file.stem
                # Check if filename is a date (YYYY-MM-DD format)
                if len(filename) == 10 and filename[4] == '-' and filename[7] == '-':
                    dates.append(filename)
            
            return sorted(dates, reverse=True)  # Most recent first
            
        except Exception as e:
            logger.error(f"Error getting available dates: {e}")
            return []
    
    def delete_data(self, path: str, date_or_filename: str) -> bool:
        """Delete stored data"""
        try:
            filepath = self.base_dir / path / f"{date_or_filename}.json"
            
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted: {filepath}")
                return True
            else:
                logger.warning(f"File not found for deletion: {filepath}")
                return False
                
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def get_all_data_summary(self) -> Dict:
        """Get summary of all stored data"""
        try:
            summary = {}
            
            paths_to_check = {
                'nse_current': 'nse/current',
                'nse_upcoming': 'nse/upcoming',
                'nse_subscription': 'nse/subscription',
                'predictions_gmp': 'predictions/gmp',
                'predictions_math': 'predictions/math',
                'predictions_ai': 'predictions/ai',
                'predictions_final': 'predictions/final_prediction'
            }
            
            for key, path in paths_to_check.items():
                dir_path = self.base_dir / path
                if dir_path.exists():
                    files = list(dir_path.glob("*.json"))
                    dates = self.get_available_dates(path)
                    
                    summary[key] = {
                        'path': str(path),
                        'total_files': len(files),
                        'available_dates': dates[:5],  # Show only 5 most recent
                        'total_dates': len(dates),
                        'latest_date': dates[0] if dates else None,
                        'oldest_date': dates[-1] if dates else None
                    }
                else:
                    summary[key] = {
                        'path': str(path),
                        'status': 'directory_not_found'
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {}
    
    def cleanup_old_files(self, path: str, keep_days: int = 30) -> int:
        """Cleanup old files, keeping only recent ones"""
        try:
            dir_path = self.base_dir / path
            if not dir_path.exists():
                return 0
            
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            deleted_count = 0
            for file in dir_path.glob("*.json"):
                try:
                    # Check file modification time
                    file_time = datetime.fromtimestamp(file.stat().st_mtime)
                    
                    if file_time < cutoff_date:
                        file.unlink()
                        deleted_count += 1
                        logger.info(f"Cleaned up old file: {file}")
                        
                except Exception as e:
                    logger.warning(f"Error cleaning up {file}: {e}")
                    continue
            
            logger.info(f"Cleanup completed: {deleted_count} files deleted from {path}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0

# Create singleton instance
file_storage = FileStorage()