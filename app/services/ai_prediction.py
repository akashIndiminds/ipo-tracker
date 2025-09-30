# app/services/ai_prediction.py

import logging
import json
import os
from google import genai
from google.genai import types
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class AIPredictionService:
    """AI Prediction using Gemini with REAL Web Research"""
    
    def __init__(self):
        self.api_key = "AIzaSyCJbiFWnGgkE7R0d18jA0PdMZfvy5XIK7g"
        os.environ['GEMINI_API_KEY'] = self.api_key
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash-exp"
        self.data_base_path = Path("C:/Akash/ipo_tracker/data")
        
        logger.info(f"Initialized Gemini AI with Google Search grounding: {self.model_name}")
    
    def load_current_ipos_only(self, date: str) -> List[Dict]:
        """Load only current IPO data - NO subscription data"""
        try:
            current_file = self.data_base_path / "nse" / "current" / f"{date}.json"
            
            if not current_file.exists():
                logger.warning(f"Current IPO file not found: {current_file}")
                return []
            
            with open(current_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
                if isinstance(file_data, list):
                    current_ipos = file_data
                elif isinstance(file_data, dict):
                    current_ipos = file_data.get('data', [file_data])
                else:
                    current_ipos = []
                
                logger.info(f"Loaded {len(current_ipos)} current IPOs from {date}")
                return current_ipos
                
        except Exception as e:
            logger.error(f"Error loading current IPO data: {e}")
            return []
    
    def generate_prediction_with_research(self, ipo_data: Dict) -> Dict:
        """Generate AI prediction with REAL autonomous web research"""
        try:
            symbol = (
                ipo_data.get('symbol') or 
                ipo_data.get('Symbol') or 
                ipo_data.get('SYMBOL') or 
                'UNKNOWN'
            )
            
            company_name = (
                ipo_data.get('company_name') or
                ipo_data.get('companyName') or
                ipo_data.get('company') or
                symbol
            )
            
            issue_price = ipo_data.get('issue_price') or ipo_data.get('issuePrice') or 'N/A'
            issue_size = ipo_data.get('issue_size') or ipo_data.get('issueSize') or 'N/A'
            issue_start = ipo_data.get('issue_start_date') or ipo_data.get('issueStartDate') or 'N/A'
            issue_end = ipo_data.get('issue_end_date') or ipo_data.get('issueEndDate') or 'N/A'
            status = ipo_data.get('status') or ipo_data.get('Status') or 'Unknown'
            lot_size = ipo_data.get('lot_size') or ipo_data.get('lotSize') or 'N/A'
            face_value = ipo_data.get('face_value') or ipo_data.get('faceValue') or 'N/A'
            
            # Concise prompt - let AI do the research
            prompt = f"""Analyze this Indian IPO using live internet data:

**IPO DETAILS:**
Company: {company_name} ({symbol})
Price: ₹{issue_price}
Size: {issue_size}
Period: {issue_start} to {issue_end}
Status: {status}

**RESEARCH & ANALYZE:**
1. Search for company financials, business model, revenue
2. Find current subscription status (QIB/NII/Retail numbers)
3. Check competitor valuations and sector trends
4. Look for expert reviews and market sentiment
5. Verify data from NSE, Moneycontrol, Economic Times

**RULES:**
- Use ONLY verified data from web research
- NEVER mention Grey Market Premium (GMP)
- If IPO is in future and no data exists, clearly state "INSUFFICIENT_DATA"
- Be realistic with gain predictions (-30% to +150%)
- Cross-verify subscription numbers from multiple sources

**Return ONLY this JSON:**
{{
    "recommendation": "BUY/HOLD/AVOID/INSUFFICIENT_DATA",
    "expected_gain_percent": <number>,
    "confidence": "HIGH/MEDIUM/LOW",
    "reasoning": "<4-5 lines covering fundamentals, valuation, subscription, sector, risks>",
    "risk_level": "LOW/MEDIUM/HIGH",
    "key_factors": ["factor1", "factor2", "factor3", "factor4", "factor5"],
    "subscription_analysis": "<Current subscription status with actual numbers if found>",
    "sector_outlook": "<Industry trends and positioning>"
}}

Research now and provide analysis."""
            
            # CRITICAL: Enable Google Search grounding
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,  # Lower for more factual responses
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                    response_modalities=["TEXT"],
                    # Enable Google Search - THIS IS THE KEY FIX
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            # Extract text from response
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Log search queries used (if available)
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    logger.info(f"Search performed for {symbol}: {candidate.grounding_metadata}")
            
            ai_data = self._parse_response(response_text)
            
            # Validate and return structured data
            return {
                'symbol': symbol,
                'company_name': company_name,
                'source': 'AI_GEMINI_SEARCH',
                'model': self.model_name,
                'recommendation': ai_data.get('recommendation', 'HOLD'),
                'expected_gain_percent': float(ai_data.get('expected_gain_percent', 0)),
                'confidence': ai_data.get('confidence', 'MEDIUM'),
                'risk_level': ai_data.get('risk_level', 'MEDIUM'),
                'reasoning': ai_data.get('reasoning', 'Analysis completed with web research'),
                'key_factors': ai_data.get('key_factors', []),
                'subscription_analysis': ai_data.get('subscription_analysis', 'Researched from internet'),
                'sector_outlook': ai_data.get('sector_outlook', ''),
                'ipo_details': {
                    'issue_price': str(issue_price),
                    'issue_size': str(issue_size),
                    'lot_size': str(lot_size),
                    'face_value': str(face_value),
                    'issue_period': f"{issue_start} to {issue_end}",
                    'status': str(status)
                },
                'subscription_summary': {
                    'total': 'Researched via AI',
                    'qib': 'Researched via AI',
                    'nii': 'Researched via AI',
                    'retail': 'Researched via AI'
                },
                'timestamp': datetime.now().isoformat(),
                'prediction_date': datetime.now().strftime('%Y-%m-%d'),
                'search_enabled': True
            }
            
        except Exception as e:
            logger.error(f"AI prediction error for {symbol}: {e}", exc_info=True)
            return self._default_prediction(symbol, str(e))
    
    def predict_all_ipos(self, date: str = None) -> List[Dict]:
        """Generate predictions for all current IPOs - with REAL web research"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            logger.info(f"🔍 Starting Google Search-powered prediction for date: {date}")
            
            # Load ONLY current IPO data
            current_ipos = self.load_current_ipos_only(date)
            
            if not current_ipos:
                logger.warning(f"No IPO data found for date: {date}")
                return []
            
            logger.info(f"Found {len(current_ipos)} IPOs - AI will research each via Google Search")
            predictions = []
            
            for idx, ipo in enumerate(current_ipos, 1):
                try:
                    symbol = (
                        ipo.get('symbol') or 
                        ipo.get('Symbol') or 
                        f'IPO_{idx}'
                    )
                    
                    logger.info(f"🔎 Processing {idx}/{len(current_ipos)}: {symbol} - Starting Google Search...")
                    
                    prediction = self.generate_prediction_with_research(ipo)
                    predictions.append(prediction)
                    
                    logger.info(f"✅ Research completed for {symbol}: {prediction['recommendation']}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing IPO {idx}: {e}", exc_info=True)
                    continue
            
            logger.info(f"🎯 Successfully generated {len(predictions)} search-powered predictions")
            return predictions
            
        except Exception as e:
            logger.error(f"Error in predict_all_ipos: {e}", exc_info=True)
            return []
    
    def _parse_response(self, text: str) -> Dict:
        """Parse Gemini AI response - handles JSON extraction"""
        try:
            clean = text.strip()
            
            # Remove markdown code blocks
            if clean.startswith('```json'):
                clean = clean[7:]
            elif clean.startswith('```'):
                clean = clean[3:]
            
            if clean.endswith('```'):
                clean = clean[:-3]
            
            clean = clean.strip()
            
            # Try to find JSON object in text
            start_idx = clean.find('{')
            end_idx = clean.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = clean[start_idx:end_idx+1]
                parsed = json.loads(json_str)
                return parsed
            
            # If no JSON found, try parsing entire text
            parsed = json.loads(clean)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.error(f"Response text: {text[:500]}")
            
            # Try to extract data from text format
            return self._extract_from_text(text)
        except Exception as e:
            logger.error(f"Response parse error: {e}")
            return {}
    
    def _extract_from_text(self, text: str) -> Dict:
        """Fallback: Extract data from non-JSON text response"""
        try:
            default_data = {
                'recommendation': 'HOLD',
                'expected_gain_percent': 0,
                'confidence': 'LOW',
                'risk_level': 'MEDIUM',
                'reasoning': text[:500] if len(text) > 500 else text,
                'key_factors': ['Analysis incomplete'],
                'subscription_analysis': 'Data extraction failed',
                'sector_outlook': 'N/A'
            }
            
            # Try to extract recommendation
            text_upper = text.upper()
            if 'BUY' in text_upper:
                default_data['recommendation'] = 'BUY'
            elif 'AVOID' in text_upper:
                default_data['recommendation'] = 'AVOID'
            elif 'INSUFFICIENT' in text_upper:
                default_data['recommendation'] = 'INSUFFICIENT_DATA'
            
            return default_data
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {}
    
    def _default_prediction(self, symbol: str, error: str = '') -> Dict:
        """Default prediction when AI fails"""
        return {
            'symbol': symbol,
            'company_name': symbol,
            'source': 'AI_GEMINI_SEARCH',
            'model': self.model_name,
            'recommendation': 'INSUFFICIENT_DATA',
            'expected_gain_percent': 0.0,
            'confidence': 'LOW',
            'risk_level': 'HIGH',
            'reasoning': f'Unable to complete research: {error}' if error else 'Research failed',
            'key_factors': ['Research incomplete', 'Data unavailable'],
            'subscription_analysis': 'Unable to fetch subscription data',
            'sector_outlook': 'N/A',
            'ipo_details': {},
            'subscription_summary': {},
            'timestamp': datetime.now().isoformat(),
            'prediction_date': datetime.now().strftime('%Y-%m-%d'),
            'error': True,
            'search_enabled': True
        }

# Singleton instance
ai_prediction_service = AIPredictionService()