# app/routes/gmp_routes.py

from fastapi import APIRouter, Path, Query
from datetime import datetime
from ..services.gmp_service import gmp_service
from ..utils.file_storage import file_storage
from typing import Optional

router = APIRouter(prefix="/api/gmp", tags=["GMP"])

@router.post("/fetch")
async def fetch_gmp_data():
    """Fetch current GMP data from both sources and create combined data"""
    result = gmp_service.fetch_current_gmp()
    return result

@router.get("/predict/{symbol}")
async def get_gmp_prediction(
    symbol: str = Path(...),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format for historical data")
):
    """Get GMP data for symbol with optional date support"""
    prediction = gmp_service.get_gmp_prediction(symbol, {}, date)
    
    # Save individual prediction
    save_date = date or datetime.now().strftime('%Y-%m-%d')
    file_storage.save_data(f"gmp/predictions/{symbol}_{save_date}", prediction)
    
    return prediction

@router.post("/scrape-sources")
async def scrape_all_gmp_sources():
    """NEW ENDPOINT: Scrape data from both GMP sources separately"""
    try:
        # Scrape both sources
        source_data = gmp_service.scrape_all_sources()
        
        if not source_data['success']:
            return source_data
        
        # Save source data separately
        save_result = gmp_service.save_source_data(source_data)
        
        return {
            'success': True,
            'message': 'Successfully scraped both GMP sources',
            'timestamp': source_data['timestamp'],
            'date': source_data['date'],
            'source_data': source_data,
            'save_result': save_result
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@router.post("/create-combined/{date}")
async def create_combined_gmp_for_date(
    date: str = Path(..., description="Date in YYYY-MM-DD format")
):
    """NEW ENDPOINT: Create combined GMP data for specific date"""
    try:
        combined_data = gmp_service.create_combined_gmp_data(date)
        
        return {
            'success': True,
            'message': f'Successfully created combined GMP data for {date}',
            'timestamp': combined_data['timestamp'],
            'date': date,
            'total_unique_ipos': combined_data.get('total_unique_ipos', 0),
            'source_counts': combined_data.get('source_counts', {}),
            'sources_available': combined_data.get('sources_available', []),
            'combined_data': combined_data
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'date': date
        }