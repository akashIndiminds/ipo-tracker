# app/routes/predict_routes.py

from fastapi import APIRouter, Path
from ..services.final_prediction import final_prediction_service
from ..services.gmp_service import gmp_service
from ..services.math_prediction import math_prediction_service
from ..services.ai_prediction import ai_prediction_service
from ..services.nse_service import nse_service
from ..utils.file_storage import file_storage

router = APIRouter(prefix="/api/predict", tags=["Final Prediction"])

@router.get("/{symbol}")
async def get_final_prediction(symbol: str = Path(...)):
    """Get combined prediction from all 3 sources"""
    # Get IPO data
    current_ipos = nse_service.fetch_current_ipos()
    ipo_data = next((ipo for ipo in current_ipos if ipo['symbol'] == symbol.upper()), {})
    
    if not ipo_data:
        return {"error": f"IPO {symbol} not found"}
    
    # Get subscription data
    subscription_data = nse_service.fetch_ipo_active_category(symbol)
    
    # Get all 3 predictions
    gmp_pred = gmp_service.get_gmp_prediction(symbol, ipo_data)
    math_pred = math_prediction_service.predict(ipo_data, subscription_data)
    ai_pred = ai_prediction_service.predict(ipo_data, subscription_data)
    
    # Combine predictions
    final_pred = final_prediction_service.combine_predictions(
        gmp_pred, math_pred, ai_pred, ipo_data
    )
    
    # Save final prediction
    file_storage.save_data(f"predictions/final/{symbol}", final_pred)
    
    return final_pred

@router.post("/all")
async def process_all_ipos():
    """Process all current IPOs and generate predictions"""
    # Get current IPOs
    current_ipos = nse_service.fetch_current_ipos()
    
    if not current_ipos:
        return {"error": "No current IPOs found"}
    
    # First fetch GMP data
    gmp_result = gmp_service.fetch_last_month_gmp()
    if gmp_result['success']:
        file_storage.save_data("gmp/raw", gmp_result['data'])
    
    results = []
    
    for ipo in current_ipos:
        symbol = ipo.get('symbol', '')
        if not symbol:
            continue
        
        try:
            # Get subscription data
            subscription_data = nse_service.fetch_ipo_active_category(symbol)
            
            # Get all predictions
            gmp_pred = gmp_service.get_gmp_prediction(symbol, ipo)
            math_pred = math_prediction_service.predict(ipo, subscription_data)
            ai_pred = ai_prediction_service.predict(ipo, subscription_data)
            
            # Combine
            final_pred = final_prediction_service.combine_predictions(
                gmp_pred, math_pred, ai_pred, ipo
            )
            
            # Save
            file_storage.save_data(f"predictions/final/{symbol}", final_pred)
            
            results.append({
                'symbol': symbol,
                'company': ipo.get('company_name'),
                'recommendation': final_pred.get('final_recommendation'),
                'expected_gain': final_pred.get('expected_gain_percent'),
                'risk': final_pred.get('risk_level')
            })
            
        except Exception as e:
            results.append({
                'symbol': symbol,
                'error': str(e)
            })
    
    # Save all results
    file_storage.save_data("predictions/final/all", {
        'total_processed': len(results),
        'results': results
    })
    
    return {
        'success': True,
        'total_processed': len(results),
        'results': results
    }

