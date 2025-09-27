# app/routes/gmp_routes.py

from fastapi import APIRouter, Path
from ..services.gmp_service import gmp_service
from ..services.nse_service import nse_service
from ..utils.file_storage import file_storage

router = APIRouter(prefix="/api/gmp", tags=["GMP"])

@router.post("/fetch")
async def fetch_gmp_data():
    """Fetch last month GMP data"""
    result = gmp_service.fetch_last_month_gmp()
    if result['success']:
        file_storage.save_data("gmp/raw", result['data'])
    return result

@router.get("/predict/{symbol}")
async def get_gmp_prediction(symbol: str = Path(...)):
    """Get GMP's own prediction"""
    # Get current IPO data
    current_ipos = nse_service.fetch_current_ipos()
    ipo_data = next((ipo for ipo in current_ipos if ipo['symbol'] == symbol.upper()), {})
    
    prediction = gmp_service.get_gmp_prediction(symbol, ipo_data)
    file_storage.save_data(f"gmp/predictions/{symbol}", prediction)
    return prediction