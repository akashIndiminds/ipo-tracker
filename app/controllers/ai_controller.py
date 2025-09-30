# app/controllers/ai_controller.py - FIXED STORAGE

from typing import Dict, List, Optional
import logging
from datetime import datetime
from pathlib import Path
import json
from ..services.ai_prediction import ai_prediction_service
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class AIController:
    """AI Controller - Handles request/response for AI predictions with FIXED storage"""
    
    def __init__(self):
        # REMOVED: Don't create separate base path
        # Let file_storage handle everything
        pass
    
    async def predict_all_current_ipos(self, date: Optional[str] = None) -> Dict:
        """
        Generate predictions for all current IPOs
        Request: No body required
        Response: All predictions with metadata
        """
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Generating AI predictions for date: {date}")
            
            # Generate predictions using service
            predictions = ai_prediction_service.predict_all_ipos(date)
            
            if not predictions:
                return {
                    'success': False,
                    'message': f'No IPO data available for date: {date}',
                    'date': date,
                    'total_predictions': 0,
                    'predictions': []
                }
            
            # Prepare response data
            result = {
                'success': True,
                'message': 'AI Predictions generated successfully',
                'date': date,
                'total_predictions': len(predictions),
                'predictions': predictions,
                'timestamp': datetime.now().isoformat()
            }
            
            # FIXED: Save predictions to data/predictions/ai/{date}.json
            save_success = file_storage.save_data("predictions/ai", result, date)
            
            if save_success:
                logger.info(f"✅ AI predictions saved to data/predictions/ai/{date}.json")
                result['storage_path'] = f'data/predictions/ai/{date}.json'
            else:
                logger.error(f"❌ Failed to save AI predictions")
                result['storage_warning'] = 'Predictions generated but not saved to file'
            
            return result
            
        except Exception as e:
            logger.error(f"Error in predict_all_current_ipos: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate predictions',
                'predictions': []
            }
    
    async def get_predictions_by_date(self, date: str) -> Dict:
        """
        Get all AI predictions for a specific date
        Request: date as path parameter
        Response: All predictions for that date
        """
        try:
            # FIXED: Load from data/predictions/ai/{date}.json
            stored_data = file_storage.load_data("predictions/ai", date)
            
            if not stored_data:
                return {
                    'success': False,
                    'message': f'No AI predictions found for date: {date}',
                    'date': date,
                    'predictions': [],
                    'suggestion': f'Generate predictions first using POST /api/ai/predict?date={date}'
                }
            
            # Return the stored data
            return stored_data.get('data', stored_data)
            
        except Exception as e:
            logger.error(f"Error retrieving predictions by date: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to retrieve predictions for date: {date}',
                'predictions': []
            }
    
    async def get_prediction_by_symbol_and_date(self, symbol: str, date: str) -> Dict:
        """
        Get AI prediction for specific symbol and date
        Request: symbol and date as path parameters
        Response: Single prediction if found
        """
        try:
            # FIXED: Load from data/predictions/ai/{date}.json
            stored_data = file_storage.load_data("predictions/ai", date)
            
            if not stored_data:
                return {
                    'success': False,
                    'message': f'No AI predictions found for date: {date}',
                    'symbol': symbol,
                    'date': date,
                    'prediction': None,
                    'suggestion': f'Generate predictions first using POST /api/ai/predict?date={date}'
                }
            
            # Extract predictions list
            predictions_list = stored_data.get('data', {}).get('predictions', [])
            if not predictions_list:
                predictions_list = stored_data.get('predictions', [])
            
            # Find prediction for symbol
            prediction = next(
                (p for p in predictions_list if p.get('symbol', '').upper() == symbol.upper()),
                None
            )
            
            if not prediction:
                return {
                    'success': False,
                    'message': f'No AI prediction found for symbol: {symbol} on date: {date}',
                    'symbol': symbol,
                    'date': date,
                    'prediction': None,
                    'available_symbols': [p.get('symbol') for p in predictions_list[:10]]
                }
            
            return {
                'success': True,
                'message': 'AI Prediction retrieved successfully',
                'symbol': symbol,
                'date': date,
                'prediction': prediction
            }
            
        except Exception as e:
            logger.error(f"Error retrieving prediction by symbol and date: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to retrieve prediction for {symbol}',
                'symbol': symbol,
                'date': date,
                'prediction': None
            }

# Create controller instance
ai_controller = AIController()