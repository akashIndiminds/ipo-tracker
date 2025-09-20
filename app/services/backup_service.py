
# app/services/backup_service.py

import json
import os
import boto3
from datetime import datetime
from typing import Dict, List

class BackupService:
    def __init__(self):
        self.local_backup_dir = "backups"
        os.makedirs(self.local_backup_dir, exist_ok=True)
        
        # AWS S3 configuration (optional)
        self.s3_client = None
        self.s3_bucket = "ipo-tracker-backups"
        
        try:
            self.s3_client = boto3.client('s3')
        except:
            print("S3 not configured, using local backups only")
    
    def backup_ipo_data(self, current_ipos: List[Dict], upcoming_ipos: List[Dict], past_ipos: List[Dict]):
        """Backup all IPO data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_data = {
            'timestamp': timestamp,
            'current_ipos': current_ipos,
            'upcoming_ipos': upcoming_ipos,
            'past_ipos': past_ipos,
            'total_records': len(current_ipos) + len(upcoming_ipos) + len(past_ipos)
        }
        
        # Local backup
        backup_file = os.path.join(self.local_backup_dir, f"ipo_data_{timestamp}.json")
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        # S3 backup (if configured)
        if self.s3_client:
            try:
                self.s3_client.upload_file(
                    backup_file,
                    self.s3_bucket,
                    f"ipo_data/{timestamp}.json"
                )
                print(f"Backup uploaded to S3: {timestamp}")
            except Exception as e:
                print(f"S3 backup failed: {e}")
        
        # Cleanup old local backups (keep last 10)
        self._cleanup_old_backups()
        
        return backup_file
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Remove old backup files"""
        backup_files = [f for f in os.listdir(self.local_backup_dir) if f.endswith('.json')]
        backup_files.sort(reverse=True)
        
        if len(backup_files) > keep_count:
            for old_file in backup_files[keep_count:]:
                try:
                    os.remove(os.path.join(self.local_backup_dir, old_file))
                except:
                    pass
