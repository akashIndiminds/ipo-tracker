# app/services/ipo_prediction_engine.py (MODIFIED - Remove GMP)
"""IPO Mathematical Prediction Engine - PURE MATH ONLY (NO GMP)"""

import math
import statistics
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """IPO Prediction Result - Pure Mathematical"""
    symbol: str
    company_name: str
    recommendation: str  # BUY, HOLD, AVOID
    risk_level: str  # LOW, MEDIUM, HIGH
    confidence_score: float  # 0-100
    expected_listing_gain: float  # Percentage (calculated without GMP)
    expected_listing_price: float
    risk_factors: List
    positive_factors: List
    mathematical_score: float
    subscription_score: float
    fundamental_score: float
    market_score: float
    final_score: float
    investment_advice: str

class IPOPredictionEngine:
    """PURE Mathematical IPO Prediction Engine (NO GMP)"""
    
    def __init__(self):
        # Pure math weights (NO GMP)
        self.WEIGHTS = {
            'subscription_rate': 0.35,      # Subscription is most important without GMP
            'company_fundamentals': 0.25,   # Company metrics
            'market_conditions': 0.20,      # Market sentiment
            'issue_details': 0.10,          # Issue size/price analysis
            'timing_factor': 0.10           # IPO timing
        }
        
        # Thresholds remain same
        self.THRESHOLDS = {
            'buy_threshold': 70,
            'hold_threshold': 50,
            'avoid_threshold': 50
        }
    
    def predict_ipo_performance(self, 
                              ipo_data: Dict, 
                              subscription_data: Optional[Dict] = None,
                              market_data: Optional[Dict] = None) -> PredictionResult:
        """
        PURE Mathematical IPO Performance Prediction (NO GMP USED)
        
        Args:
            ipo_data: Basic IPO information from NSE
            subscription_data: Subscription details
            market_data: Market conditions data
            
        NO GMP DATA PARAMETER!
        """
        
        symbol = ipo_data.get('symbol', 'UNKNOWN')
        company_name = ipo_data.get('company_name', 'Unknown Company')
        
        logger.info(f"Pure Math Analysis for: {symbol} - {company_name}")
        
        # Calculate PURE MATH scores (NO GMP)
        scores = {
            'subscription_score': self._calculate_subscription_score(subscription_data) if subscription_data else 40,
            'fundamental_score': self._calculate_fundamental_score(ipo_data),
            'market_score': self._calculate_market_score(market_data) if market_data else 50,
            'timing_score': self._calculate_timing_score(ipo_data),
            'technical_score': self._calculate_technical_score(ipo_data, subscription_data)
        }
        
        # Calculate final weighted score (PURE MATH)
        final_score = self._calculate_final_score_math(scores)
        
        # Generate prediction based on MATH ONLY
        recommendation, risk_level, confidence = self._generate_recommendation_math(final_score, scores)
        
        # Calculate expected returns (WITHOUT GMP)
        expected_gain, expected_price = self._calculate_expected_returns_math(
            ipo_data, subscription_data, final_score
        )
        
        # Identify factors
        risk_factors = self._identify_risk_factors_math(ipo_data, subscription_data, scores)
        positive_factors = self._identify_positive_factors_math(ipo_data, subscription_data, scores)
        
        # Generate investment advice
        investment_advice = self._generate_investment_advice(recommendation, risk_level, expected_gain)
        
        return PredictionResult(
            symbol=symbol,
            company_name=company_name,
            recommendation=recommendation,
            risk_level=risk_level,
            confidence_score=confidence,
            expected_listing_gain=expected_gain,
            expected_listing_price=expected_price,
            risk_factors=risk_factors,
            positive_factors=positive_factors,
            mathematical_score=scores['technical_score'],
            subscription_score=scores['subscription_score'],
            fundamental_score=scores['fundamental_score'],
            market_score=scores['market_score'],
            final_score=final_score,
            investment_advice=investment_advice
        )
    
    def _calculate_subscription_score(self, subscription_data: Dict) -> float:
        """Calculate subscription-based score (0-100) - PURE MATH"""
        try:
            total_subscription = subscription_data.get('total_subscription', 0)
            
            # Base score from overall subscription
            if total_subscription >= 50:
                base_score = 95
            elif total_subscription >= 30:
                base_score = 90
            elif total_subscription >= 15:
                base_score = 85
            elif total_subscription >= 10:
                base_score = 80
            elif total_subscription >= 5:
                base_score = 70
            elif total_subscription >= 3:
                base_score = 60
            elif total_subscription >= 2:
                base_score = 50
            elif total_subscription >= 1:
                base_score = 40
            else:
                base_score = 20
            
            # Category-wise bonus
            categories = subscription_data.get('categories', {})
            category_bonus = 0
            
            for category_name, category_data in categories.items():
                subscription_times = category_data.get('subscription_times', 0)
                
                if 'retail' in category_name.lower():
                    if subscription_times >= 5:
                        category_bonus += 10
                    elif subscription_times >= 3:
                        category_bonus += 5
                
                elif 'qib' in category_name.lower():
                    if subscription_times >= 3:
                        category_bonus += 15
                    elif subscription_times >= 1.5:
                        category_bonus += 8
                
                elif 'hni' in category_name.lower():
                    if subscription_times >= 5:
                        category_bonus += 8
                    elif subscription_times >= 2:
                        category_bonus += 4
            
            return min(100, base_score + category_bonus)
            
        except Exception as e:
            logger.error(f"Error calculating subscription score: {e}")
            return 40
    
    def _calculate_fundamental_score(self, ipo_data: Dict) -> float:
        """Calculate fundamental analysis score - PURE MATH"""
        try:
            score = 50  # Base neutral score
            
            # Issue price analysis
            issue_price_text = ipo_data.get('issue_price', '')
            issue_price = self._extract_max_price(issue_price_text)
            
            if issue_price:
                if issue_price <= 150:
                    score += 20  # Very affordable
                elif issue_price <= 300:
                    score += 15
                elif issue_price <= 500:
                    score += 10
                elif issue_price <= 800:
                    score += 5
                else:
                    score -= 10  # Too expensive
            
            # Issue size analysis
            issue_size_text = ipo_data.get('issue_size', '')
            issue_size = self._extract_number(issue_size_text)
            
            if issue_size:
                if issue_size <= 300:  # Small issue
                    score += 15
                elif issue_size <= 800:  # Medium issue
                    score += 10
                elif issue_size <= 2000:  # Large issue
                    score += 5
                else:  # Very large issue
                    score -= 5
            
            # Series analysis (SME vs Mainboard)
            series = ipo_data.get('series', 'EQ')
            if series == 'SME':
                score += 10  # SME IPOs often have higher listing gains
            
            # Status analysis
            status = ipo_data.get('status', '').lower()
            if 'open' in status or 'active' in status:
                score += 5
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"Error calculating fundamental score: {e}")
            return 50
    
    def _calculate_market_score(self, market_data: Dict) -> float:
        """Calculate market conditions score - PURE MATH"""
        try:
            score = 50  # Base score
            
            # Check market status
            for market in market_data.get('data', []):
                market_status = market.get('market_status', '').lower()
                if 'open' in market_status:
                    score += 10
                elif 'closed' in market_status:
                    score -= 5
            
            # Add general market sentiment (can be enhanced)
            score += 10  # Assuming neutral to positive market
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"Error calculating market score: {e}")
            return 50
    
    def _calculate_timing_score(self, ipo_data: Dict) -> float:
        """Calculate IPO timing score - PURE MATH"""
        try:
            score = 60  # Base score
            
            # Current month analysis
            current_month = datetime.now().month
            
            # Good months for IPO (post-budget, festive season)
            if current_month in [4, 5, 10, 11]:  # April, May, Oct, Nov
                score += 15
            # Quarter-end months (volatile)
            elif current_month in [3, 6, 9, 12]:
                score -= 10
            # Start of year (fresh allocations)
            elif current_month in [1, 2]:
                score += 10
            
            # Day of week analysis
            current_day = datetime.now().weekday()
            if current_day in [1, 2, 3]:  # Tuesday, Wednesday, Thursday
                score += 5
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"Error calculating timing score: {e}")
            return 60
    
    def _calculate_technical_score(self, ipo_data: Dict, subscription_data: Optional[Dict]) -> float:
        """Calculate technical indicators - PURE MATH"""
        try:
            score = 50
            
            # Subscription momentum
            if subscription_data:
                total_sub = subscription_data.get('total_subscription', 0)
                
                if total_sub > 10:
                    score += 25  # Very strong momentum
                elif total_sub > 5:
                    score += 15  # Strong momentum
                elif total_sub > 2:
                    score += 10  # Good momentum
                elif total_sub < 1:
                    score -= 15  # Weak momentum
            
            # Price band width analysis
            issue_price_text = ipo_data.get('issue_price', '')
            if '-' in issue_price_text:
                prices = re.findall(r'[\d.]+', issue_price_text)
                if len(prices) >= 2:
                    min_price = float(prices[0])
                    max_price = float(prices[1])
                    band_width = ((max_price - min_price) / min_price) * 100
                    
                    if band_width <= 5:
                        score += 10  # Tight band (confidence)
                    elif band_width <= 10:
                        score += 5
                    else:
                        score -= 5  # Wide band (uncertainty)
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return 50
    
    def _calculate_final_score_math(self, scores: Dict[str, float]) -> float:
        """Calculate weighted final score - PURE MATH"""
        try:
            # Pure math weighted scoring (NO GMP)
            final_score = (
                scores['subscription_score'] * 0.35 +    # 35% weight
                scores['fundamental_score'] * 0.25 +     # 25% weight
                scores['market_score'] * 0.20 +          # 20% weight
                scores['timing_score'] * 0.10 +          # 10% weight
                scores['technical_score'] * 0.10         # 10% weight
            )
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating final score: {e}")
            return 50
    
    def _generate_recommendation_math(self, final_score: float, scores: Dict) -> Tuple[str, str, float]:
        """Generate recommendation based on PURE MATH"""
        
        # Base recommendation
        if final_score >= self.THRESHOLDS['buy_threshold']:
            recommendation = 'BUY'
            confidence = min(90, final_score)
        elif final_score >= self.THRESHOLDS['hold_threshold']:
            recommendation = 'HOLD'
            confidence = min(70, final_score)
        else:
            recommendation = 'AVOID'
            confidence = min(60, 100 - final_score)
        
        # Risk level based on subscription and fundamentals
        subscription_score = scores.get('subscription_score', 50)
        fundamental_score = scores.get('fundamental_score', 50)
        
        if subscription_score >= 70 and fundamental_score >= 70:
            risk_level = 'LOW'
        elif subscription_score >= 50 and fundamental_score >= 50:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
        
        return recommendation, risk_level, confidence
    
    def _calculate_expected_returns_math(self, ipo_data: Dict, 
                                        subscription_data: Optional[Dict],
                                        final_score: float) -> Tuple[float, float]:
        """Calculate expected returns WITHOUT GMP"""
        try:
            issue_price_text = ipo_data.get('issue_price', '')
            issue_price = self._extract_max_price(issue_price_text)
            
            if not issue_price:
                return 0, 0
            
            # Base gain calculation from pure math score
            # Score 50 = 0% gain, Score 100 = 30% gain, Score 0 = -15% gain
            base_gain = ((final_score - 50) / 50) * 30
            
            # Subscription adjustment
            if subscription_data:
                total_sub = subscription_data.get('total_subscription', 0)
                
                if total_sub > 20:
                    base_gain += 10  # High demand bonus
                elif total_sub > 10:
                    base_gain += 5
                elif total_sub < 1:
                    base_gain -= 10  # Low demand penalty
            
            # SME bonus
            if ipo_data.get('series') == 'SME':
                base_gain += 5
            
            # Cap the gains realistically
            expected_gain = max(-20, min(50, base_gain))
            
            # Calculate expected listing price
            expected_price = issue_price * (1 + expected_gain / 100)
            
            return round(expected_gain, 2), round(expected_price, 2)
            
        except Exception as e:
            logger.error(f"Error calculating expected returns: {e}")
            return 0, 0
    
    def _identify_risk_factors_math(self, ipo_data: Dict, 
                                   subscription_data: Optional[Dict],
                                   scores: Dict) -> List[str]:
        """Identify risk factors - PURE MATH"""
        risk_factors = []
        
        # Subscription risks
        if subscription_data:
            total_subscription = subscription_data.get('total_subscription', 0)
            if total_subscription < 1:
                risk_factors.append(f"Undersubscribed at {total_subscription:.2f}x - weak demand")
            elif total_subscription < 2:
                risk_factors.append(f"Low subscription at {total_subscription:.2f}x")
        
        # Price risks
        issue_price = self._extract_max_price(ipo_data.get('issue_price', ''))
        if issue_price and issue_price > 1000:
            risk_factors.append(f"Very high issue price ₹{issue_price}")
        
        # Size risks
        issue_size = self._extract_number(ipo_data.get('issue_size', ''))
        if issue_size and issue_size > 3000:
            risk_factors.append(f"Large issue size ₹{issue_size}Cr")
        
        # Score-based risks
        if scores.get('subscription_score', 0) < 40:
            risk_factors.append("Poor subscription metrics")
        
        if scores.get('fundamental_score', 0) < 40:
            risk_factors.append("Weak fundamental indicators")
        
        if scores.get('market_score', 0) < 40:
            risk_factors.append("Unfavorable market conditions")
        
        return risk_factors
    
    def _identify_positive_factors_math(self, ipo_data: Dict,
                                       subscription_data: Optional[Dict],
                                       scores: Dict) -> List[str]:
        """Identify positive factors - PURE MATH"""
        positive_factors = []
        
        # Subscription positives
        if subscription_data:
            total_subscription = subscription_data.get('total_subscription', 0)
            
            if total_subscription > 10:
                positive_factors.append(f"Excellent subscription at {total_subscription:.1f}x")
            elif total_subscription > 5:
                positive_factors.append(f"Strong subscription at {total_subscription:.1f}x")
            elif total_subscription > 2:
                positive_factors.append(f"Good subscription at {total_subscription:.1f}x")
        
        # Price positives
        issue_price = self._extract_max_price(ipo_data.get('issue_price', ''))
        if issue_price and issue_price <= 200:
            positive_factors.append(f"Affordable issue price ₹{issue_price}")
        
        # Size positives
        issue_size = self._extract_number(ipo_data.get('issue_size', ''))
        if issue_size and issue_size <= 500:
            positive_factors.append(f"Small issue size ₹{issue_size}Cr - better price discovery")
        
        # Series positives
        if ipo_data.get('series') == 'SME':
            positive_factors.append("SME IPO - historically better listing gains")
        
        # Score-based positives
        if scores.get('subscription_score', 0) > 70:
            positive_factors.append("Strong demand indicators")
        
        if scores.get('fundamental_score', 0) > 70:
            positive_factors.append("Good fundamental metrics")
        
        if scores.get('timing_score', 0) > 70:
            positive_factors.append("Favorable IPO timing")
        
        return positive_factors
    
    def _generate_investment_advice(self, recommendation: str, risk_level: str, expected_gain: float) -> str:
        """Generate investment advice - PURE MATH BASED"""
        advice_parts = []
        
        if recommendation == 'BUY':
            advice_parts.append("🟢 RECOMMENDED (Based on Mathematical Analysis)")
            if risk_level == 'LOW':
                advice_parts.append("✅ Low risk - suitable for conservative investors")
            elif risk_level == 'MEDIUM':
                advice_parts.append("⚠️ Medium risk - moderate allocation suggested")
            else:
                advice_parts.append("⚠️ High risk - only for risk-takers")
                
        elif recommendation == 'HOLD':
            advice_parts.append("🟡 NEUTRAL (Mathematical indicators mixed)")
            advice_parts.append("📊 Wait for better clarity or apply minimum")
            
        else:  # AVOID
            advice_parts.append("🔴 NOT RECOMMENDED (Poor mathematical indicators)")
            advice_parts.append("❌ Multiple risk factors present")
        
        if expected_gain > 15:
            advice_parts.append(f"📈 Expected gain {expected_gain}% based on mathematical model")
        elif expected_gain > 5:
            advice_parts.append(f"📊 Moderate gain {expected_gain}% expected")
        elif expected_gain > 0:
            advice_parts.append(f"📉 Low gain {expected_gain}% expected")
        else:
            advice_parts.append(f"⚠️ Risk of {abs(expected_gain)}% loss")
        
        return " | ".join(advice_parts)
    
    # Helper methods remain same
    def _extract_number(self, text: str) -> Optional[float]:
        if not text:
            return None
        try:
            clean_text = re.sub(r'[₹,\s]', '', str(text).strip())
            number_match = re.search(r'[\d.]+', clean_text)
            if number_match:
                return float(number_match.group())
            return None
        except Exception:
            return None
    
    def _extract_max_price(self, price_text: str) -> Optional[float]:
        if not price_text:
            return None
        try:
            prices = re.findall(r'[\d.]+', price_text)
            if len(prices) >= 2:
                return float(prices[-1])
            elif len(prices) == 1:
                return float(prices[0])
            return None
        except Exception:
            return None

# Create prediction engine instance
ipo_prediction_engine = IPOPredictionEngine()