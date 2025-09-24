# app/controllers/local_controller.py
"""Local Controller - Handles locally stored JSON data requests"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
from fastapi import HTTPException

from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class LocalController:
    """Local Controller - Serves data from stored JSON files"""
    
    def __init__(self):
        self.file_storage = file_storage
    
    async def get_stored_current_ipos(self, date: str = None) -> Dict[str, Any]:
        """Get current IPOs from stored JSON file"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Loading stored current IPOs for date: {date}")
            
            # Load data from file
            stored_data = self.file_storage.load_data('current_ipos', date)
            
            if not stored_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No current IPOs data found for date: {date}"
                )
            
            data = stored_data.get('data', [])
            metadata = stored_data.get('metadata', {})
            
            return {
                'success': True,
                'message': f'Successfully loaded current IPOs for {date}',
                'date': date,
                'count': len(data) if isinstance(data, list) else 1,
                'data': data,
                'metadata': metadata,
                'source': 'LOCAL_STORAGE',
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local controller error - current IPOs for {date}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load current IPOs for {date}: {str(e)}"
            )
    
    async def get_stored_upcoming_ipos(self, date: str = None) -> Dict[str, Any]:
        """Get upcoming IPOs from stored JSON file"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Loading stored upcoming IPOs for date: {date}")
            
            # Load data from file
            stored_data = self.file_storage.load_data('upcoming_ipos', date)
            
            if not stored_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No upcoming IPOs data found for date: {date}"
                )
            
            data = stored_data.get('data', [])
            metadata = stored_data.get('metadata', {})
            
            return {
                'success': True,
                'message': f'Successfully loaded upcoming IPOs for {date}',
                'date': date,
                'count': len(data) if isinstance(data, list) else 1,
                'data': data,
                'metadata': metadata,
                'source': 'LOCAL_STORAGE',
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local controller error - upcoming IPOs for {date}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load upcoming IPOs for {date}: {str(e)}"
            )
    
    async def get_stored_market_status(self, date: str = None) -> Dict[str, Any]:
        """Get market status from stored JSON file"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Loading stored market status for date: {date}")
            
            # Load data from file
            stored_data = self.file_storage.load_data('market_status', date)
            
            if not stored_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No market status data found for date: {date}"
                )
            
            data = stored_data.get('data', [])
            metadata = stored_data.get('metadata', {})
            
            return {
                'success': True,
                'message': f'Successfully loaded market status for {date}',
                'date': date,
                'count': len(data) if isinstance(data, list) else 1,
                'data': data,
                'metadata': metadata,
                'source': 'LOCAL_STORAGE',
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local controller error - market status for {date}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load market status for {date}: {str(e)}"
            )
    
    async def get_stored_active_category(self, symbol: str = None, date: str = None) -> Dict[str, Any]:
        """Get IPO active category from stored JSON file"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Loading stored active category for date: {date}, symbol: {symbol}")
            
            # Load data from file
            stored_data = self.file_storage.load_data('active_category', date)
            
            if not stored_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No active category data found for date: {date}"
                )
            
            data = stored_data.get('data', {})
            metadata = stored_data.get('metadata', {})
            
            # If specific symbol requested
            if symbol:
                if symbol not in data:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No active category data found for symbol: {symbol} on date: {date}"
                    )
                
                return {
                    'success': True,
                    'message': f'Successfully loaded active category for {symbol} on {date}',
                    'date': date,
                    'symbol': symbol,
                    'data': data[symbol],
                    'metadata': metadata,
                    'source': 'LOCAL_STORAGE',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Return all symbols
            return {
                'success': True,
                'message': f'Successfully loaded all active categories for {date}',
                'date': date,
                'count': len(data),
                'symbols': list(data.keys()) if isinstance(data, dict) else [],
                'data': data,
                'metadata': metadata,
                'source': 'LOCAL_STORAGE',
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local controller error - active category for {symbol} on {date}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load active category data: {str(e)}"
            )
    
    async def get_available_dates(self, data_type: str) -> Dict[str, Any]:
        """Get list of available dates for a data type"""
        try:
            logger.info(f"Getting available dates for data type: {data_type}")
            
            valid_types = ['current_ipos', 'upcoming_ipos', 'market_status', 'active_category']
            if data_type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data type. Valid types: {valid_types}"
                )
            
            dates = self.file_storage.get_available_dates(data_type)
            
            return {
                'success': True,
                'message': f'Found {len(dates)} available dates for {data_type}',
                'data_type': data_type,
                'available_dates': dates,
                'count': len(dates),
                'latest_date': dates[0] if dates else None,
                'oldest_date': dates[-1] if dates else None,
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local controller error - available dates for {data_type}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get available dates: {str(e)}"
            )
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of all stored data"""
        try:
            logger.info("Getting data summary")
            
            summary = self.file_storage.get_all_data_summary()
            
            if not summary:
                return {
                    'success': False,
                    'message': 'No stored data found',
                    'summary': {},
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'success': True,
                'message': 'Successfully loaded data summary',
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Local controller error - data summary: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get data summary: {str(e)}"
            )
    
    async def delete_stored_data(self, data_type: str, date: str) -> Dict[str, Any]:
        """Delete stored data for specific date"""
        try:
            logger.info(f"Deleting stored data: {data_type} for {date}")
            
            valid_types = ['current_ipos', 'upcoming_ipos', 'market_status', 'active_category']
            if data_type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data type. Valid types: {valid_types}"
                )
            
            deleted = self.file_storage.delete_data(data_type, date)
            
            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail=f"No data found to delete for {data_type} on {date}"
                )
            
            return {
                'success': True,
                'message': f'Successfully deleted {data_type} data for {date}',
                'data_type': data_type,
                'date': date,
                'deleted': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local controller error - delete data {data_type} for {date}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete data: {str(e)}"
            )
    
    async def cleanup_old_data(self, data_type: str, keep_days: int = 30) -> Dict[str, Any]:
        """Cleanup old stored data"""
        try:
            logger.info(f"Cleaning up old data for {data_type}, keeping {keep_days} days")
            
            valid_types = ['current_ipos', 'upcoming_ipos', 'market_status', 'active_category']
            if data_type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data type. Valid types: {valid_types}"
                )
            
            deleted_count = self.file_storage.cleanup_old_files(data_type, keep_days)
            
            return {
                'success': True,
                'message': f'Cleanup completed for {data_type}',
                'data_type': data_type,
                'keep_days': keep_days,
                'deleted_files': deleted_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Local controller error - cleanup {data_type}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cleanup data: {str(e)}"
            )

# Create controller instance
local_controller = LocalController()