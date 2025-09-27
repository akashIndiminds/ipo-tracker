# app/services/math_prediction.py

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MathPredictionService:
    """Pure Mathematical Prediction - No GMP involved"""
    
    def predict(self, ipo_data: Dict, subscription_data: Optional[Dict] = None) -> Dict:
        """Pure math prediction based on subscription and fundamentals"""
        try:
            symbol = ipo_data.get('symbol', 'UNKNOWN')
            
            # Calculate scores
            subscription_score = self._calculate_subscription_score(subscription_data)
            fundamental_score = self._calculate_fundamental_score(ipo_data)
            market_score = 50  # Default neutral
            
            # Final score (pure math)
            final_score = (
                subscription_score * 0.5 +  # 50% weight to subscription
                fundamental_score * 0.3 +   # 30% weight to fundamentals  
                market_score * 0.2          # 20% weight to market
            )
            
            # Calculate expected gain based on score
            # Score 0-100 maps to -20% to +30% gain
            expected_gain = ((final_score - 50) / 50) * 30
            
            # Get recommendation
            if final_score >= 70:
                recommendation = 'BUY'
            elif final_score >= 50:
                recommendation = 'HOLD'
            else:
                recommendation = 'AVOID'
            
            return {
                'symbol': symbol,
                'source': 'MATH',
                'final_score': round(final_score, 2),
                'expected_gain_percent': round(expected_gain, 2),
                'recommendation': recommendation,
                'confidence': self._get_confidence(final_score),
                'scores': {
                    'subscription': subscription_score,
                    'fundamental': fundamental_score,
                    'market': market_score
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Math prediction error: {e}")
            return self._default_prediction(ipo_data.get('symbol', 'UNKNOWN'))
    
    def _calculate_subscription_score(self, subscription_data: Optional[Dict]) -> float:
        """Calculate subscription-based score"""
        if not subscription_data:
            return 40  # Default low score
        
        total_sub = subscription_data.get('total_subscription', 0)
        
        if total_sub >= 20:
            return 95
        elif total_sub >= 10:
            return 85
        elif total_sub >= 5:
            return 75
        elif total_sub >= 3:
            return 65
        elif total_sub >= 2:
            return 55
        elif total_sub >= 1:
            return 45
        else:
            return 30
    
    def _calculate_fundamental_score(self, ipo_data: Dict) -> float:
        """Calculate fundamental score"""
        score = 50  # Base score
        
        # Price analysis
        price_text = ipo_data.get('issue_price', '')
        if price_text:
            import re
            prices = re.findall(r'[\d.]+', price_text)
            if prices:
                max_price = float(prices[-1])
                if max_price <= 200:
                    score += 20
                elif max_price <= 500:
                    score += 10
                elif max_price > 1000:
                    score -= 10
        
        # SME bonus
        if ipo_data.get('series') == 'SME':
            score += 15
        
        return min(100, max(0, score))
    
    def _get_confidence(self, score: float) -> str:
        """Get confidence level"""
        if score >= 80:
            return 'HIGH'
        elif score >= 60:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _default_prediction(self, symbol: str) -> Dict:
        """Default prediction on error"""
        return {
            'symbol': symbol,
            'source': 'MATH',
            'final_score': 50,
            'expected_gain_percent': 0,
            'recommendation': 'HOLD',
            'confidence': 'LOW',
            'timestamp': datetime.now().isoformat()
        }

math_prediction_service = MathPredictionService()
