# app/controllers/ai_controller.py

from typing import Dict, List, Optional
import logging
from datetime import datetime
from pathlib import Path
import json
from ..services.ai_prediction import ai_prediction_service
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class AIController:
    """AI Controller - Handles request/response for AI predictions"""
    
    def __init__(self):
        self.prediction_base_path = Path("C:/Akash/ipo_tracker/data/predictions/ai")
        self.prediction_base_path.mkdir(parents=True, exist_ok=True)
    
    async def predict_all_current_ipos(self, date: Optional[str] = None) -> Dict:
        """
        Generate predictions for all current IPOs
        Request: No body required
        Response: All predictions with metadata
        """
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Generating predictions for date: {date}")
            
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
            
            # Save predictions to file
            self._save_predictions(date, predictions)
            
            return {
                'success': True,
                'message': 'Predictions generated successfully',
                'date': date,
                'total_predictions': len(predictions),
                'predictions': predictions,
                'timestamp': datetime.now().isoformat()
            }
            
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
            prediction_file = self.prediction_base_path / f"{date}.json"
            
            if not prediction_file.exists():
                return {
                    'success': False,
                    'message': f'No predictions found for date: {date}',
                    'date': date,
                    'predictions': []
                }
            
            with open(prediction_file, 'r', encoding='utf-8') as f:
                predictions = json.load(f)
            
            return {
                'success': True,
                'message': 'Predictions retrieved successfully',
                'date': date,
                'total_predictions': len(predictions),
                'predictions': predictions
            }
            
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
            prediction_file = self.prediction_base_path / f"{date}.json"
            
            if not prediction_file.exists():
                return {
                    'success': False,
                    'message': f'No predictions found for date: {date}',
                    'symbol': symbol,
                    'date': date,
                    'prediction': None
                }
            
            with open(prediction_file, 'r', encoding='utf-8') as f:
                predictions = json.load(f)
            
            # Find prediction for symbol
            prediction = next(
                (p for p in predictions if p.get('symbol', '').upper() == symbol.upper()),
                None
            )
            
            if not prediction:
                return {
                    'success': False,
                    'message': f'No prediction found for symbol: {symbol} on date: {date}',
                    'symbol': symbol,
                    'date': date,
                    'prediction': None
                }
            
            return {
                'success': True,
                'message': 'Prediction retrieved successfully',
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
    
    def _save_predictions(self, date: str, predictions: List[Dict]) -> None:
        """Save predictions to file (overwrites existing file for same date)"""
        try:
            prediction_file = self.prediction_base_path / f"{date}.json"
            
            # Always overwrite - no append logic
            with open(prediction_file, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Predictions saved to: {prediction_file}")
            
        except Exception as e:
            logger.error(f"Error saving predictions: {e}")

ai_controller = AIController()