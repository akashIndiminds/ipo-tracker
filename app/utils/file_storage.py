# app/utils/file_storage.py

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FileStorage:
    """Organized file storage by type and date"""
    
    def __init__(self):
        self.base_dir = Path("data")
        self._create_directories()
    
    def _create_directories(self):
        """Create organized directory structure"""
        dirs = [
            "nse/current", "nse/upcoming", "nse/subscription",
            "gmp/raw", "gmp/predictions",
            "predictions/math", "predictions/ai", "predictions/final"
        ]
        for dir_path in dirs:
            (self.base_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    def save_data(self, path: str, data: Dict, date: str = None) -> bool:
        """Save data to organized path"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            filepath = self.base_dir / path / f"{date}.json"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            save_data = {
                'metadata': {
                    'path': path,
                    'date': date,
                    'timestamp': datetime.now().isoformat()
                },
                'data': data
            }
            
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            logger.info(f"Saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Save failed: {e}")
            return False
    
    def load_data(self, path: str, date: str = None) -> Optional[Dict]:
        """Load data from organized path"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            filepath = self.base_dir / path / f"{date}.json"
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Load failed: {e}")
            return None

file_storage = FileStorage()
