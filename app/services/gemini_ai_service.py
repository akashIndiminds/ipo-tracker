# app/services/gemini_ai_service.py
"""Gemini AI Service - AI-based IPO predictions"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import google.generativeai as genai
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class GeminiAIService:
    """Gemini AI for IPO predictions"""
    
    def __init__(self):
        # Configure Gemini API
        self.api_key = "AIzaSyCJbiFWnGgkE7Rxxxxxxxxxxxxxxxxxxxx"
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Storage for AI predictions
        self.predictions_cache = {}
    
    def analyze_ipo_with_ai(self, ipo_data: Dict, subscription_data: Optional[Dict] = None) -> Dict:
        """
        Send IPO data to Gemini AI for analysis
        
        Returns JSON prediction from AI
        """
        try:
            symbol = ipo_data.get('symbol', 'UNKNOWN')
            logger.info(f"Getting AI prediction for {symbol}")
            
            # Prepare prompt for Gemini
            prompt = self._create_ai_prompt(ipo_data, subscription_data)
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            ai_prediction = self._parse_ai_response(response.text, symbol, ipo_data)
            
            # Store in cache
            self.predictions_cache[symbol] = ai_prediction
            
            # Save to file
            self._save_ai_predictions()
            
            return ai_prediction
            
        except Exception as e:
            logger.error(f"Gemini AI error for {symbol}: {e}")
            return self._get_default_prediction(symbol, ipo_data)
    
    def analyze_all_current_ipos(self, current_ipos: List[Dict]) -> Dict[str, Any]:
        """
        Analyze all current IPOs with AI
        
        Processes one by one and stores all predictions
        """
        logger.info(f"Analyzing {len(current_ipos)} IPOs with Gemini AI")
        
        all_predictions = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'total_analyzed': 0,
            'predictions': {}
        }
        
        for ipo in current_ipos:
            symbol = ipo.get('symbol', '')
            if not symbol:
                continue
            
            try:
                # Get AI prediction for each IPO
                ai_result = self.analyze_ipo_with_ai(ipo)
                
                # Store with short symbol as key
                short_symbol = self._get_short_symbol(symbol)
                all_predictions['predictions'][short_symbol] = ai_result
                all_predictions['total_analyzed'] += 1
                
                logger.info(f"AI analysis complete for {symbol}")
                
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")
                continue
        
        # Save all predictions to file
        self._save_all_ai_predictions(all_predictions)
        
        return all_predictions
    
    def _create_ai_prompt(self, ipo_data: Dict, subscription_data: Optional[Dict]) -> str:
        """
        Create detailed prompt for Gemini AI
        
        NO GMP DATA - AI should do its own research and analysis
        """
        
        prompt = f"""
You are an expert IPO analyst. Analyze this IPO and provide a prediction WITHOUT using Grey Market Premium (GMP) data.
Use your knowledge of market conditions, company fundamentals, and IPO trends to predict listing performance.

IPO DETAILS:
- Company: {ipo_data.get('company_name', 'Unknown')}
- Symbol: {ipo_data.get('symbol', 'Unknown')}
- Issue Price: {ipo_data.get('issue_price', 'Unknown')}
- Issue Size: {ipo_data.get('issue_size', 'Unknown')}
- Series: {ipo_data.get('series', 'EQ')}
- Status: {ipo_data.get('status', 'Unknown')}
- Issue Start Date: {ipo_data.get('issue_start_date', 'Unknown')}
- Issue End Date: {ipo_data.get('issue_end_date', 'Unknown')}
"""

        if subscription_data:
            prompt += f"""
SUBSCRIPTION DATA:
- Total Subscription: {subscription_data.get('total_subscription', 0)}x
- Categories: {json.dumps(subscription_data.get('categories', {}), indent=2)}
"""

        prompt += """

TASK:
Based on the above information and your knowledge of:
1. Current market conditions
2. Industry trends
3. Company fundamentals
4. Historical IPO performance patterns
5. Investor sentiment

Provide your prediction in EXACTLY this JSON format (no additional text):
{
    "symbol": "SHORT_SYMBOL_NAME",
    "recommendation": "BUY/HOLD/AVOID",
    "expected_listing_gain_percent": 15.5,
    "expected_listing_price": 125.50,
    "confidence_score": 75,
    "risk_level": "LOW/MEDIUM/HIGH",
    "ai_reasoning": "Brief explanation of your analysis",
    "key_factors": [
        "Factor 1",
        "Factor 2",
        "Factor 3"
    ],
    "market_sentiment": "POSITIVE/NEUTRAL/NEGATIVE",
    "sector_outlook": "STRONG/MODERATE/WEAK",
    "listing_day_volume": "HIGH/MEDIUM/LOW",
    "price_target_3_months": 150.00,
    "price_target_6_months": 180.00
}

IMPORTANT: 
- Do NOT use or mention GMP data
- Base your analysis on market research and fundamentals
- Provide realistic predictions based on actual market conditions
- Return ONLY valid JSON, no other text
"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str, symbol: str, ipo_data: Dict) -> Dict:
        """
        Parse Gemini AI response and ensure valid JSON
        """
        try:
            # Clean response text (remove markdown if any)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            # Parse JSON
            ai_data = json.loads(cleaned_text.strip())
            
            # Ensure all required fields
            result = {
                'symbol': self._get_short_symbol(symbol),
                'company_name': ipo_data.get('company_name', ''),
                'recommendation': ai_data.get('recommendation', 'HOLD'),
                'expected_listing_gain_percent': float(ai_data.get('expected_listing_gain_percent', 0)),
                'expected_listing_price': float(ai_data.get('expected_listing_price', 0)),
                'confidence_score': float(ai_data.get('confidence_score', 50)),
                'risk_level': ai_data.get('risk_level', 'MEDIUM'),
                'ai_reasoning': ai_data.get('ai_reasoning', ''),
                'key_factors': ai_data.get('key_factors', []),
                'market_sentiment': ai_data.get('market_sentiment', 'NEUTRAL'),
                'sector_outlook': ai_data.get('sector_outlook', 'MODERATE'),
                'listing_day_volume': ai_data.get('listing_day_volume', 'MEDIUM'),
                'price_target_3_months': float(ai_data.get('price_target_3_months', 0)),
                'price_target_6_months': float(ai_data.get('price_target_6_months', 0)),
                'ai_generated_at': datetime.now().isoformat(),
                'source': 'GEMINI_AI'
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response for {symbol}: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return self._get_default_prediction(symbol, ipo_data)
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._get_default_prediction(symbol, ipo_data)
    
    def _get_short_symbol(self, symbol: str) -> str:
        """
        Get short symbol name for storage
        
        Examples:
        SOLARWORLD -> SOLAR
        GKENERGY -> GKENE
        """
        if len(symbol) <= 5:
            return symbol.upper()
        
        # Take first 5 characters
        return symbol[:5].upper()
    
    def _get_default_prediction(self, symbol: str, ipo_data: Dict) -> Dict:
        """
        Default prediction if AI fails
        """
        return {
            'symbol': self._get_short_symbol(symbol),
            'company_name': ipo_data.get('company_name', ''),
            'recommendation': 'HOLD',
            'expected_listing_gain_percent': 5.0,
            'expected_listing_price': 0,
            'confidence_score': 30,
            'risk_level': 'HIGH',
            'ai_reasoning': 'AI analysis failed - default prediction',
            'key_factors': ['Insufficient data'],
            'market_sentiment': 'NEUTRAL',
            'sector_outlook': 'MODERATE',
            'listing_day_volume': 'MEDIUM',
            'price_target_3_months': 0,
            'price_target_6_months': 0,
            'ai_generated_at': datetime.now().isoformat(),
            'source': 'DEFAULT'
        }
    
    def _save_ai_predictions(self):
        """
        Save current predictions to file
        """
        try:
            data = {
                'predictions': self.predictions_cache,
                'last_updated': datetime.now().isoformat(),
                'total_predictions': len(self.predictions_cache)
            }
            
            file_storage.save_data('ai_predictions_cache', data)
            logger.info(f"Saved {len(self.predictions_cache)} AI predictions")
            
        except Exception as e:
            logger.error(f"Failed to save AI predictions: {e}")
    
    def _save_all_ai_predictions(self, all_predictions: Dict):
        """
        Save all AI predictions to dedicated file
        """
        try:
            file_storage.save_data('gemini_ai_predictions', all_predictions)
            logger.info(f"Saved all AI predictions to file")
            
        except Exception as e:
            logger.error(f"Failed to save all AI predictions: {e}")
    
    def load_ai_predictions(self) -> Dict[str, Any]:
        """
        Load saved AI predictions from file
        """
        try:
            data = file_storage.load_data('gemini_ai_predictions')
            
            if data and 'data' in data:
                return data['data']
            
            return {'predictions': {}, 'success': False}
            
        except Exception as e:
            logger.error(f"Failed to load AI predictions: {e}")
            return {'predictions': {}, 'success': False}
    
    def get_ai_prediction_for_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Get AI prediction for specific symbol
        """
        # Try cache first
        short_symbol = self._get_short_symbol(symbol)
        if short_symbol in self.predictions_cache:
            return self.predictions_cache[short_symbol]
        
        # Try loading from file
        saved_data = self.load_ai_predictions()
        predictions = saved_data.get('predictions', {})
        
        if short_symbol in predictions:
            return predictions[short_symbol]
        
        # Check with full symbol
        if symbol in predictions:
            return predictions[symbol]
        
        return None

# Create service instance
gemini_ai_service = GeminiAIService()
