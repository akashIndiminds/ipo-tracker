# app/routes/gmp_history_routes.py
"""GMP History Routes - Last 3 months GMP data endpoints"""

from fastapi import APIRouter, Path, Query
from typing import Dict, Any

from ..controllers.gmp_history_controller import gmp_history_controller

# Create router
router = APIRouter(prefix="/api/gmp/history", tags=["GMP History (Last 3 Months)"])

@router.post("/fetch-and-store")
async def fetch_and_store_gmp_history() -> Dict[str, Any]:
    """
    Fetch and Store Last 3 Months GMP Data
    
    This endpoint:
    - Scrapes IPOWatch for current GMP data
    - Filters only last 3 months IPOs
    - Stores data in structured JSON format
    - Uses symbol as key for easy access
    """
    return await gmp_history_controller.fetch_and_store_gmp_history()

@router.get("/data")
async def get_stored_gmp_history() -> Dict[str, Any]:
    """
    Get Stored Last 3 Months GMP History Data
    
    Returns:
    - Complete stored GMP data
    - Metadata about collection
    - Symbol-based JSON structure
    """
    return await gmp_history_controller.get_stored_gmp_history()

@router.get("/summary")
async def get_gmp_summary() -> Dict[str, Any]:
    """
    Get GMP History Summary Statistics
    
    Returns:
    - Summary statistics (avg GMP, gains, etc.)
    - Top performers by expected gain
    - Positive/negative GMP distribution
    - Data collection info
    """
    return await gmp_history_controller.get_gmp_summary()

@router.get("/search/{symbol}")
async def search_ipo_by_symbol(
    symbol: str = Path(..., description="IPO symbol to search (e.g., GKENERGY)")
) -> Dict[str, Any]:
    """
    Search IPO by Symbol
    
    Searches stored GMP data for specific IPO:
    - Exact symbol match first
    - Partial match fallback
    - Returns complete IPO data if found
    """
    return await gmp_history_controller.search_ipo_by_symbol(symbol)

@router.get("/update-status")
async def get_update_status() -> Dict[str, Any]:
    """
    Get Data Update Status
    
    Returns information about:
    - Last data collection timestamp
    - Data freshness
    - Total IPOs stored
    - Date range coverage
    """
    try:
        from ..utils.file_storage import file_storage
        from datetime import datetime
        
        # Get file info for gmp_history_3months
        file_info = file_storage.get_file_info('gmp_history_3months')
        
        if not file_info:
            return {
                'success': False,
                'message': 'No GMP history data found',
                'data_available': False,
                'last_update': None,
                'freshness_hours': None
            }
        
        metadata = file_info.get('metadata', {})
        
        # Calculate data freshness
        collection_timestamp = metadata.get('collection_timestamp')
        freshness_hours = None
        
        if collection_timestamp:
            try:
                collection_time = datetime.fromisoformat(collection_timestamp)
                freshness_hours = round((datetime.now() - collection_time).total_seconds() / 3600, 1)
            except:
                pass
        
        return {
            'success': True,
            'message': 'Data status retrieved successfully',
            'data_available': True,
            'file_info': {
                'size_mb': file_info.get('size_mb'),
                'created_at': file_info.get('created_at'),
                'modified_at': file_info.get('modified_at')
            },
            'data_info': {
                'total_ipos': metadata.get('total_ipos', 0),
                'collection_date': metadata.get('collection_date'),
                'date_range': metadata.get('date_range', {}),
                'source': metadata.get('source')
            },
            'freshness': {
                'last_update': collection_timestamp,
                'hours_old': freshness_hours,
                'is_fresh': freshness_hours < 24 if freshness_hours else False,
                'needs_update': freshness_hours > 48 if freshness_hours else True
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to get update status'
        }
    