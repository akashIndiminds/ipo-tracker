# app/services/ai_prediction.py

import logging
import json
import google.generativeai as genai
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AIPredictionService:
    """AI Prediction using Gemini"""
    
    def __init__(self):
        self.api_key = "AIzaSyCJbiFWnGgkE7R0d18jA0PdMZfvy5XIK7g"
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def predict(self, ipo_data: Dict, subscription_data: Optional[Dict] = None) -> Dict:
        """Get AI prediction for IPO"""
        try:
            symbol = ipo_data.get('symbol', 'UNKNOWN')
            
            prompt = f"""
            Analyze this IPO and predict listing performance:
            
            Company: {ipo_data.get('company_name')}
            Symbol: {symbol}
            Price: {ipo_data.get('issue_price')}
            Size: {ipo_data.get('issue_size')}
            Status: {ipo_data.get('status')}
            
            Subscription: {subscription_data.get('total_subscription', 0) if subscription_data else 'N/A'}x
            
            Return ONLY JSON:
            {{
                "recommendation": "BUY/HOLD/AVOID",
                "expected_gain_percent": 10.5,
                "confidence": "HIGH/MEDIUM/LOW",
                "reasoning": "Brief reason"
            }}
            """
            
            response = self.model.generate_content(prompt)
            ai_data = self._parse_response(response.text)
            
            return {
                'symbol': symbol,
                'source': 'AI',
                'recommendation': ai_data.get('recommendation', 'HOLD'),
                'expected_gain_percent': ai_data.get('expected_gain_percent', 0),
                'confidence': ai_data.get('confidence', 'MEDIUM'),
                'reasoning': ai_data.get('reasoning', ''),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI prediction error: {e}")
            return self._default_prediction(ipo_data.get('symbol', 'UNKNOWN'))
    
    def _parse_response(self, text: str) -> Dict:
        """Parse AI response"""
        try:
            # Clean response
            clean = text.strip()
            if clean.startswith('```json'):
                clean = clean[7:]
            if clean.startswith('```'):
                clean = clean[3:]
            if clean.endswith('```'):
                clean = clean[:-3]
            
            return json.loads(clean.strip())
        except:
            return {}
    
    def _default_prediction(self, symbol: str) -> Dict:
        """Default AI prediction"""
        return {
            'symbol': symbol,
            'source': 'AI',
            'recommendation': 'HOLD',
            'expected_gain_percent': 0,
            'confidence': 'LOW',
            'reasoning': 'AI analysis failed',
            'timestamp': datetime.now().isoformat()
        }

ai_prediction_service = AIPredictionService()
