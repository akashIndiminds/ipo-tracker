# app/services/final_prediction.py

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FinalPredictionService:
    """Combines GMP, Math, and AI predictions"""
    
    def combine_predictions(self, 
                           gmp_pred: Dict, 
                           math_pred: Dict, 
                           ai_pred: Dict,
                           ipo_data: Dict) -> Dict:
        """Combine all 3 predictions into final recommendation"""
        try:
            symbol = ipo_data.get('symbol', 'UNKNOWN')
            
            # Weights for each prediction source
            weights = {
                'gmp': 0.4 if gmp_pred.get('has_data') else 0,
                'math': 0.3,
                'ai': 0.3
            }
            
            # Normalize weights if GMP has no data
            if weights['gmp'] == 0:
                weights['math'] = 0.5
                weights['ai'] = 0.5
            
            # Calculate weighted average gain
            total_gain = (
                gmp_pred.get('expected_gain_percent', 0) * weights['gmp'] +
                math_pred.get('expected_gain_percent', 0) * weights['math'] +
                ai_pred.get('expected_gain_percent', 0) * weights['ai']
            )
            
            # Determine final recommendation
            recommendations = {
                'BUY': 0,
                'HOLD': 0,
                'AVOID': 0
            }
            
            # Count recommendations
            for pred in [gmp_pred, math_pred, ai_pred]:
                rec = pred.get('recommendation', 'HOLD')
                if 'BUY' in rec:
                    recommendations['BUY'] += 1
                elif 'AVOID' in rec:
                    recommendations['AVOID'] += 1
                else:
                    recommendations['HOLD'] += 1
            
            # Final recommendation based on majority
            if recommendations['BUY'] >= 2:
                final_rec = 'BUY'
            elif recommendations['AVOID'] >= 2:
                final_rec = 'AVOID'
            else:
                final_rec = 'HOLD'
            
            # Calculate risk level
            if total_gain > 15 and final_rec == 'BUY':
                risk = 'LOW'
            elif total_gain < 5 or final_rec == 'AVOID':
                risk = 'HIGH'
            else:
                risk = 'MEDIUM'
            
            # Calculate expected listing price
            issue_price = self._extract_price(ipo_data.get('issue_price', ''))
            expected_listing = issue_price * (1 + total_gain/100) if issue_price else 0
            
            return {
                'symbol': symbol,
                'company_name': ipo_data.get('company_name', ''),
                'final_recommendation': final_rec,
                'expected_gain_percent': round(total_gain, 2),
                'expected_listing_price': round(expected_listing, 2),
                'risk_level': risk,
                'predictions': {
                    'gmp': {
                        'has_data': gmp_pred.get('has_data', False),
                        'gain': gmp_pred.get('expected_gain_percent', 0),
                        'recommendation': gmp_pred.get('recommendation', 'NO_DATA')
                    },
                    'math': {
                        'gain': math_pred.get('expected_gain_percent', 0),
                        'recommendation': math_pred.get('recommendation', 'HOLD'),
                        'score': math_pred.get('final_score', 50)
                    },
                    'ai': {
                        'gain': ai_pred.get('expected_gain_percent', 0),
                        'recommendation': ai_pred.get('recommendation', 'HOLD'),
                        'reasoning': ai_pred.get('reasoning', '')
                    }
                },
                'weights_used': weights,
                'recommendation_counts': recommendations,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Final prediction error: {e}")
            return {
                'symbol': ipo_data.get('symbol', 'UNKNOWN'),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _extract_price(self, price_text: str) -> float:
        """Extract max price from price range"""
        try:
            import re
            prices = re.findall(r'[\d.]+', price_text)
            if prices:
                return float(prices[-1])
            return 0
        except:
            return 0

final_prediction_service = FinalPredictionService()
