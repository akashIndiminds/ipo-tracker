# app/utils/file_storage.py
"""File Storage Utility - Handles JSON file operations for daily data storage"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FileStorage:
    """File Storage utility for daily JSON data management"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        logger.info(f"File storage initialized: {self.data_dir.absolute()}")
    
    def _get_filename(self, data_type: str, date: str = None) -> str:
        """Generate filename based on data type and date"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        filename_map = {
            'current_ipos': f'current_ipos_{date}.json',
            'upcoming_ipos': f'upcoming_ipos_{date}.json',
            'market_status': f'market_status_{date}.json',
            'active_category': f'active_category_{date}.json'
        }
        
        return filename_map.get(data_type, f'{data_type}_{date}.json')
    
    def _get_filepath(self, data_type: str, date: str = None) -> Path:
        """Get full file path"""
        filename = self._get_filename(data_type, date)
        return self.data_dir / filename
    
    def save_data(self, data_type: str, data: List[Dict] | Dict, date: str = None) -> bool:
        """Save data to JSON file with metadata"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            filepath = self._get_filepath(data_type, date)
            
            # Prepare data with metadata
            save_data = {
                'metadata': {
                    'data_type': data_type,
                    'date': date,
                    'timestamp': datetime.now().isoformat(),
                    'records_count': len(data) if isinstance(data, list) else 1,
                    'source': 'NSE_API'
                },
                'data': data
            }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {data_type} data to {filepath} ({save_data['metadata']['records_count']} records)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save {data_type} data: {e}")
            return False
    
    def load_data(self, data_type: str, date: str = None) -> Optional[Dict]:
        """Load data from JSON file"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            filepath = self._get_filepath(data_type, date)
            
            if not filepath.exists():
                logger.warning(f"File not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            logger.info(f"Loaded {data_type} data from {filepath}")
            return loaded_data
            
        except Exception as e:
            logger.error(f"Failed to load {data_type} data for {date}: {e}")
            return None
    
    def get_available_dates(self, data_type: str) -> List[str]:
        """Get list of available dates for a data type"""
        try:
            dates = []
            pattern = self._get_filename(data_type, "*").replace("*", "")
            
            for file in self.data_dir.glob(f"*{data_type}*.json"):
                # Extract date from filename
                filename = file.stem
                if data_type in filename:
                    date_part = filename.split(f'{data_type}_')[1] if f'{data_type}_' in filename else None
                    if date_part and len(date_part) == 10:  # YYYY-MM-DD format
                        dates.append(date_part)
            
            return sorted(dates, reverse=True)  # Most recent first
            
        except Exception as e:
            logger.error(f"Failed to get available dates for {data_type}: {e}")
            return []
    
    def delete_data(self, data_type: str, date: str) -> bool:
        """Delete data file for specific date"""
        try:
            filepath = self._get_filepath(data_type, date)
            
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted {data_type} data for {date}")
                return True
            else:
                logger.warning(f"File not found for deletion: {filepath}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete {data_type} data for {date}: {e}")
            return False
    
    def get_file_info(self, data_type: str, date: str = None) -> Optional[Dict]:
        """Get file information and metadata"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            filepath = self._get_filepath(data_type, date)
            
            if not filepath.exists():
                return None
            
            # Get file stats
            stat = filepath.stat()
            
            # Load metadata
            loaded_data = self.load_data(data_type, date)
            metadata = loaded_data.get('metadata', {}) if loaded_data else {}
            
            return {
                'filename': filepath.name,
                'filepath': str(filepath.absolute()),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {data_type} - {date}: {e}")
            return None
    
    def cleanup_old_files(self, data_type: str, keep_days: int = 30) -> int:
        """Clean up old files, keeping only recent ones"""
        try:
            deleted_count = 0
            available_dates = self.get_available_dates(data_type)
            
            if len(available_dates) > keep_days:
                dates_to_delete = available_dates[keep_days:]  # Skip recent ones
                
                for date in dates_to_delete:
                    if self.delete_data(data_type, date):
                        deleted_count += 1
            
            logger.info(f"Cleanup completed for {data_type}: deleted {deleted_count} files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cleanup failed for {data_type}: {e}")
            return 0
    
    def get_all_data_summary(self) -> Dict[str, Any]:
        """Get summary of all stored data"""
        try:
            summary = {
                'data_types': ['current_ipos', 'upcoming_ipos', 'market_status', 'active_category'],
                'total_files': 0,
                'total_size_mb': 0,
                'details': {}
            }
            
            for data_type in summary['data_types']:
                dates = self.get_available_dates(data_type)
                total_size = 0
                
                for date in dates:
                    file_info = self.get_file_info(data_type, date)
                    if file_info:
                        total_size += file_info['size_mb']
                
                summary['details'][data_type] = {
                    'available_dates': dates,
                    'file_count': len(dates),
                    'total_size_mb': round(total_size, 2),
                    'latest_date': dates[0] if dates else None
                }
                
                summary['total_files'] += len(dates)
                summary['total_size_mb'] += total_size
            
            summary['total_size_mb'] = round(summary['total_size_mb'], 2)
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get data summary: {e}")
            return {}
    
    def append_to_daily_log(self, data_type: str, log_entry: Dict, date: str = None) -> bool:
        """Append log entry to daily log file"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            log_filename = f"{data_type}_log_{date}.json"
            log_filepath = self.data_dir / log_filename
            
            # Load existing log or create new
            if log_filepath.exists():
                with open(log_filepath, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
            else:
                log_data = {
                    'metadata': {
                        'log_type': f"{data_type}_log",
                        'date': date,
                        'created_at': datetime.now().isoformat()
                    },
                    'entries': []
                }
            
            # Add new entry with timestamp
            log_entry['timestamp'] = datetime.now().isoformat()
            log_data['entries'].append(log_entry)
            log_data['metadata']['last_updated'] = datetime.now().isoformat()
            log_data['metadata']['total_entries'] = len(log_data['entries'])
            
            # Save updated log
            with open(log_filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Appended log entry to {log_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to append log entry: {e}")
            return False
    
    def get_data_with_fallback(self, data_type: str, date: str = None, fallback_days: int = 7) -> Optional[Dict]:
        """Get data with fallback to previous days if current date not available"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Try to get data for requested date
            data = self.load_data(data_type, date)
            if data:
                return data
            
            # Fallback to previous days
            available_dates = self.get_available_dates(data_type)
            
            # Filter dates that are <= requested date and within fallback range
            from datetime import datetime, timedelta
            requested_date = datetime.strptime(date, "%Y-%m-%d")
            
            fallback_candidates = []
            for available_date in available_dates:
                try:
                    av_date = datetime.strptime(available_date, "%Y-%m-%d")
                    if av_date <= requested_date:
                        days_diff = (requested_date - av_date).days
                        if days_diff <= fallback_days:
                            fallback_candidates.append((available_date, days_diff))
                except:
                    continue
            
            # Sort by days difference (closest first)
            fallback_candidates.sort(key=lambda x: x[1])
            
            # Try fallback dates
            for fallback_date, days_diff in fallback_candidates:
                fallback_data = self.load_data(data_type, fallback_date)
                if fallback_data:
                    # Add fallback info to metadata
                    if 'metadata' in fallback_data:
                        fallback_data['metadata']['is_fallback'] = True
                        fallback_data['metadata']['requested_date'] = date
                        fallback_data['metadata']['actual_date'] = fallback_date
                        fallback_data['metadata']['days_difference'] = days_diff
                    
                    logger.info(f"Using fallback data from {fallback_date} for {data_type} (requested: {date})")
                    return fallback_data
            
            logger.warning(f"No data found for {data_type} on {date} or within {fallback_days} day fallback range")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get data with fallback for {data_type} - {date}: {e}")
            return None

# Create storage instance
file_storage = FileStorage()