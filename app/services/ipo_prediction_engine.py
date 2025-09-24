# app/services/ipo_prediction_engine.py
"""IPO Mathematical Prediction Engine with GMP Integration"""

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
    """IPO Prediction Result"""
    symbol: str
    company_name: str
    recommendation: str  # BUY, HOLD, AVOID
    risk_level: str  # LOW, MEDIUM, HIGH
    confidence_score: float  # 0-100
    expected_listing_gain: float  # Percentage
    expected_listing_price: float
    risk_factors: List
    positive_factors: List
    mathematical_score: float
    gmp_score: float
    subscription_score: float
    final_score: float
    investment_advice: str

class IPOPredictionEngine:
    """Mathematical IPO Prediction Engine"""
    
    def __init__(self):
        # Risk factors weights
        self.WEIGHTS = {
            'gmp_reliability': 0.25,        # GMP data reliability
            'subscription_rate': 0.20,      # Subscription ratio
            'price_band_analysis': 0.15,    # Price band vs market
            'market_conditions': 0.10,      # Overall market sentiment
            'company_fundamentals': 0.15,   # Financial health
            'sector_performance': 0.10,     # Sector trends
            'issue_size': 0.05             # Issue size impact
        }
        
        # Thresholds for recommendations
        self.THRESHOLDS = {
            'buy_threshold': 75,    # Score >= 75 = BUY
            'hold_threshold': 50,   # Score 50-74 = HOLD
            'avoid_threshold': 50   # Score < 50 = AVOID
        }
    
    def predict_ipo_performance(self, 
                              ipo_data: Dict, 
                              gmp_data: Optional[Dict] = None,
                              subscription_data: Optional[Dict] = None,
                              market_data: Optional[Dict] = None) -> PredictionResult:
        """
        Comprehensive IPO Performance Prediction
        
        Args:
            ipo_data: Basic IPO information from NSE
            gmp_data: Grey Market Premium data
            subscription_data: Subscription details
            market_data: Market conditions data
        
        Returns:
            PredictionResult with comprehensive analysis
        """
        
        symbol = ipo_data.get('symbol', 'UNKNOWN')
        company_name = ipo_data.get('company_name', 'Unknown Company')
        
        logger.info(f"Analyzing IPO: {symbol} - {company_name}")
        
        # Initialize scores
        scores = {
            'gmp_score': 0,
            'subscription_score': 0,
            'fundamental_score': 0,
            'market_score': 0,
            'risk_score': 0
        }
        
        # Calculate individual scores
        scores['gmp_score'] = self._calculate_gmp_score(gmp_data) if gmp_data else 0
        scores['subscription_score'] = self._calculate_subscription_score(subscription_data) if subscription_data else 0
        scores['fundamental_score'] = self._calculate_fundamental_score(ipo_data)
        scores['market_score'] = self._calculate_market_score(market_data) if market_data else 50
        scores['risk_score'] = self._calculate_risk_score(ipo_data, gmp_data, subscription_data)
        
        # Calculate final weighted score
        final_score = self._calculate_final_score(scores)
        
        # Generate prediction
        recommendation, risk_level, confidence = self._generate_recommendation(final_score, scores)
        
        # Calculate expected returns
        expected_gain, expected_price = self._calculate_expected_returns(ipo_data, gmp_data, final_score)
        
        # Identify factors
        risk_factors = self._identify_risk_factors(ipo_data, gmp_data, subscription_data, scores)
        positive_factors = self._identify_positive_factors(ipo_data, gmp_data, subscription_data, scores)
        
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
            mathematical_score=scores['fundamental_score'],
            gmp_score=scores['gmp_score'],
            subscription_score=scores['subscription_score'],
            final_score=final_score,
            investment_advice=investment_advice
        )
    
    def _calculate_gmp_score(self, gmp_data: Dict) -> float:
        """
        Calculate GMP-based score (0-100)
        
        GMP Analysis Formula:
        - High GMP (>20%): Good demand indicator
        - Consistent GMP across sources: Higher reliability
        - GMP trend: Increasing = positive, decreasing = negative
        """
        try:
            consensus_gmp = gmp_data.get('consensus_gmp', 0)
            consensus_gain = gmp_data.get('consensus_gain', 0)
            reliability_score = gmp_data.get('reliability_score', 0)
            
            # Base score from GMP percentage
            if consensus_gain > 30:
                base_score = 90
            elif consensus_gain > 20:
                base_score = 80
            elif consensus_gain > 10:
                base_score = 70
            elif consensus_gain > 5:
                base_score = 60
            elif consensus_gain > 0:
                base_score = 50
            elif consensus_gain > -5:
                base_score = 40
            else:
                base_score = 20
            
            # Adjust for reliability
            reliability_factor = reliability_score / 100
            adjusted_score = base_score * (0.7 + 0.3 * reliability_factor)
            
            # Check for consensus across sources
            sources = gmp_data.get('sources', {})
            if len(sources) >= 2:
                gmp_values = [s.get('gmp', 0) for s in sources.values() if s.get('gmp') is not None]
                if len(gmp_values) >= 2:
                    std_dev = statistics.stdev(gmp_values) if len(gmp_values) > 1 else 0
                    avg_gmp = statistics.mean(gmp_values)
                    
                    # Lower standard deviation means more consensus
                    if avg_gmp > 0:
                        consensus_factor = max(0.5, 1 - (std_dev / avg_gmp))
                        adjusted_score *= consensus_factor
            
            return min(100, max(0, adjusted_score))
            
        except Exception as e:
            logger.error(f"Error calculating GMP score: {e}")
            return 0
    
    def _calculate_subscription_score(self, subscription_data: Dict) -> float:
        """
        Calculate subscription-based score (0-100)
        
        Subscription Analysis:
        - Overall subscription ratio
        - Category-wise analysis (Retail, QIB, HNI)
        - Application vs allotment ratio
        """
        try:
            total_subscription = subscription_data.get('total_subscription', 0)
            categories = subscription_data.get('categories', {})
            
            # Base score from overall subscription
            if total_subscription >= 50:
                base_score = 95
            elif total_subscription >= 20:
                base_score = 90
            elif total_subscription >= 10:
                base_score = 80
            elif total_subscription >= 5:
                base_score = 70
            elif total_subscription >= 2:
                base_score = 60
            elif total_subscription >= 1:
                base_score = 50
            elif total_subscription >= 0.5:
                base_score = 30
            else:
                base_score = 10
            
            # Analyze category-wise subscription
            category_bonus = 0
            for category_name, category_data in categories.items():
                subscription_times = category_data.get('subscription_times', 0)
                
                if 'retail' in category_name.lower():
                    # Retail subscription is important
                    if subscription_times >= 5:
                        category_bonus += 10
                    elif subscription_times >= 2:
                        category_bonus += 5
                elif 'qib' in category_name.lower():
                    # QIB subscription shows institutional confidence
                    if subscription_times >= 2:
                        category_bonus += 15
                    elif subscription_times >= 1:
                        category_bonus += 8
                elif 'hni' in category_name.lower():
                    # HNI subscription shows affluent investor interest
                    if subscription_times >= 3:
                        category_bonus += 8
                    elif subscription_times >= 1:
                        category_bonus += 4
            
            final_score = min(100, base_score + category_bonus)
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating subscription score: {e}")
            return 0
    
    def _calculate_fundamental_score(self, ipo_data: Dict) -> float:
        """
        Calculate fundamental analysis score based on available IPO data
        
        Factors:
        - Issue price vs peer comparison
        - Issue size (smaller = better for retail)
        - Company age and track record
        - Valuation metrics if available
        """
        try:
            score = 50  # Base neutral score
            
            # Issue price analysis
            issue_price_text = ipo_data.get('issue_price', '')
            issue_price = self._extract_max_price(issue_price_text)
            
            if issue_price:
                # Price band analysis
                if issue_price <= 100:
                    score += 15  # Affordable for retail
                elif issue_price <= 200:
                    score += 10
                elif issue_price <= 500:
                    score += 5
                else:
                    score -= 5   # Too expensive for retail
            
            # Issue size analysis
            issue_size_text = ipo_data.get('issue_size', '')
            issue_size = self._extract_number(issue_size_text)
            
            if issue_size:
                if issue_size <= 100:  # Small issue (< 100 Cr)
                    score += 10
                elif issue_size <= 500:  # Medium issue
                    score += 5
                elif issue_size <= 1000:  # Large issue
                    score += 0
                else:  # Very large issue
                    score -= 5
            
            # Series analysis (SME vs Mainboard)
            series = ipo_data.get('series', 'EQ')
            if series == 'SME':
                score += 5  # SME IPOs often have higher listing gains
            
            # Status analysis
            status = ipo_data.get('status', '').lower()
            if 'open' in status or 'active' in status:
                score += 5
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"Error calculating fundamental score: {e}")
            return 50
    
    def _calculate_market_score(self, market_data: Dict) -> float:
        """Calculate market conditions score"""
        try:
            # Base score assuming neutral market
            score = 50
            
            # Check market status
            for market in market_data.get('data', []):
                market_status = market.get('market_status', '').lower()
                if 'open' in market_status:
                    score += 10
                elif 'closed' in market_status:
                    score -= 5
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"Error calculating market score: {e}")
            return 50
    
    def _calculate_risk_score(self, ipo_data: Dict, gmp_data: Optional[Dict], 
                            subscription_data: Optional[Dict]) -> float:
        """
        Calculate risk score (0-100, lower = more risky)
        
        Risk Factors:
        - Negative GMP
        - Low subscription
        - High issue price
        - Large issue size
        - Market volatility
        """
        try:
            risk_score = 100  # Start with lowest risk
            
            # GMP-based risks
            if gmp_data:
                consensus_gain = gmp_data.get('consensus_gain', 0)
                reliability = gmp_data.get('reliability_score', 0)
                
                if consensus_gain < 0:
                    risk_score -= 30  # Negative GMP is high risk
                elif consensus_gain < 5:
                    risk_score -= 15  # Low GMP is medium risk
                
                if reliability < 50:
                    risk_score -= 10  # Low reliability increases risk
            
            # Subscription-based risks
            if subscription_data:
                total_subscription = subscription_data.get('total_subscription', 0)
                if total_subscription < 1:
                    risk_score -= 20  # Undersubscribed is risky
                elif total_subscription < 2:
                    risk_score -= 10
            
            # Price-based risks
            issue_price_text = ipo_data.get('issue_price', '')
            issue_price = self._extract_max_price(issue_price_text)
            
            if issue_price and issue_price > 1000:
                risk_score -= 15  # Very high price is risky
            elif issue_price and issue_price > 500:
                risk_score -= 8
            
            return min(100, max(0, risk_score))
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 50
    
    def _calculate_final_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted final score"""
        try:
            # Weighted scoring
            final_score = (
                scores['gmp_score'] * 0.30 +           # GMP is most important
                scores['subscription_score'] * 0.25 +  # Subscription shows demand
                scores['fundamental_score'] * 0.20 +   # Fundamentals matter
                scores['market_score'] * 0.15 +        # Market conditions
                scores['risk_score'] * 0.10            # Risk adjustment
            )
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating final score: {e}")
            return 50
    
    def _generate_recommendation(self, final_score: float, scores: Dict) -> Tuple[str, str, float]:
        """Generate recommendation based on final score"""
        
        # Base recommendation
        if final_score >= self.THRESHOLDS['buy_threshold']:
            recommendation = 'BUY'
            confidence = min(95, final_score)
        elif final_score >= self.THRESHOLDS['hold_threshold']:
            recommendation = 'HOLD'
            confidence = min(80, final_score)
        else:
            recommendation = 'AVOID'
            confidence = min(70, 100 - final_score)
        
        # Risk level determination
        risk_score = scores.get('risk_score', 50)
        gmp_score = scores.get('gmp_score', 50)
        
        if risk_score >= 70 and gmp_score >= 70:
            risk_level = 'LOW'
        elif risk_score >= 50 and gmp_score >= 50:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'
        
        # Adjust recommendation based on risk
        if risk_level == 'HIGH' and recommendation == 'BUY':
            recommendation = 'HOLD'
            confidence *= 0.8
        
        return recommendation, risk_level, confidence
    
    def _calculate_expected_returns(self, ipo_data: Dict, gmp_data: Optional[Dict], 
                                  final_score: float) -> Tuple[float, float]:
        """Calculate expected listing gain and price"""
        
        try:
            issue_price_text = ipo_data.get('issue_price', '')
            issue_price = self._extract_max_price(issue_price_text)
            
            if not issue_price:
                return 0, 0
            
            # Base expected gain from GMP
            base_gain = 0
            if gmp_data:
                consensus_gain = gmp_data.get('consensus_gain', 0)
                reliability = gmp_data.get('reliability_score', 0)
                
                # Adjust GMP gain based on reliability
                reliability_factor = reliability / 100
                base_gain = consensus_gain * (0.6 + 0.4 * reliability_factor)
            
            # Adjust based on mathematical score
            score_adjustment = (final_score - 50) / 50  # -1 to 1 range
            
            # Conservative adjustment
            if score_adjustment > 0:
                adjusted_gain = base_gain * (1 + score_adjustment * 0.3)  # Max 30% boost
            else:
                adjusted_gain = base_gain * (1 + score_adjustment * 0.5)  # Max 50% reduction
            
            # Calculate expected listing price
            expected_price = issue_price * (1 + adjusted_gain / 100)
            
            return round(adjusted_gain, 2), round(expected_price, 2)
            
        except Exception as e:
            logger.error(f"Error calculating expected returns: {e}")
            return 0, 0
    
    def _identify_risk_factors(self, ipo_data: Dict, gmp_data: Optional[Dict], 
                             subscription_data: Optional[Dict], scores: Dict) -> List[str]:
        """Identify risk factors"""
        
        risk_factors = []
        
        # GMP-based risks
        if gmp_data:
            consensus_gain = gmp_data.get('consensus_gain', 0)
            reliability = gmp_data.get('reliability_score', 0)
            
            if consensus_gain < 0:
                risk_factors.append(f"Negative GMP of {consensus_gain}% indicates weak demand")
            elif consensus_gain < 5:
                risk_factors.append(f"Low GMP of {consensus_gain}% shows limited enthusiasm")
            
            if reliability < 50:
                risk_factors.append("Low GMP data reliability - conflicting sources")
        
        # Subscription risks
        if subscription_data:
            total_subscription = subscription_data.get('total_subscription', 0)
            if total_subscription < 1:
                risk_factors.append(f"Undersubscribed at {total_subscription:.2f}x - weak demand")
            elif total_subscription < 2:
                risk_factors.append(f"Low subscription at {total_subscription:.2f}x")
        
        # Price risks
        issue_price_text = ipo_data.get('issue_price', '')
        issue_price = self._extract_max_price(issue_price_text)
        
        if issue_price and issue_price > 1000:
            risk_factors.append(f"Very high issue price ₹{issue_price} may limit retail participation")
        elif issue_price and issue_price > 500:
            risk_factors.append(f"High issue price ₹{issue_price} for retail investors")
        
        # Size risks
        issue_size_text = ipo_data.get('issue_size', '')
        issue_size = self._extract_number(issue_size_text)
        
        if issue_size and issue_size > 2000:
            risk_factors.append(f"Large issue size ₹{issue_size}Cr may face absorption issues")
        
        # Score-based risks
        if scores.get('gmp_score', 0) < 30:
            risk_factors.append("Poor GMP performance indicates negative sentiment")
        
        if scores.get('subscription_score', 0) < 30:
            risk_factors.append("Poor subscription performance shows lack of demand")
        
        # Market timing risks
        current_month = datetime.now().month
        if current_month in [3, 9]:  # Quarter-end months
            risk_factors.append("Quarter-end timing may affect institutional participation")
        
        return risk_factors
    
    def _identify_positive_factors(self, ipo_data: Dict, gmp_data: Optional[Dict], 
                                 subscription_data: Optional[Dict], scores: Dict) -> List[str]:
        """Identify positive factors"""
        
        positive_factors = []
        
        # GMP-based positives
        if gmp_data:
            consensus_gain = gmp_data.get('consensus_gain', 0)
            reliability = gmp_data.get('reliability_score', 0)
            
            if consensus_gain > 20:
                positive_factors.append(f"Strong GMP of {consensus_gain}% shows high demand")
            elif consensus_gain > 10:
                positive_factors.append(f"Good GMP of {consensus_gain}% indicates positive sentiment")
            elif consensus_gain > 5:
                positive_factors.append(f"Positive GMP of {consensus_gain}% suggests listing gains")
            
            if reliability > 80:
                positive_factors.append("High GMP data reliability across multiple sources")
            elif reliability > 60:
                positive_factors.append("Good GMP data consistency")
        
        # Subscription positives
        if subscription_data:
            total_subscription = subscription_data.get('total_subscription', 0)
            categories = subscription_data.get('categories', {})
            
            if total_subscription > 10:
                positive_factors.append(f"Excellent subscription at {total_subscription:.1f}x")
            elif total_subscription > 5:
                positive_factors.append(f"Strong subscription at {total_subscription:.1f}x")
            elif total_subscription > 2:
                positive_factors.append(f"Good subscription at {total_subscription:.1f}x")
            
            # Check category-wise subscription
            for category_name, category_data in categories.items():
                subscription_times = category_data.get('subscription_times', 0)
                
                if subscription_times > 5:
                    positive_factors.append(f"Excellent {category_name} subscription at {subscription_times:.1f}x")
                elif subscription_times > 2:
                    positive_factors.append(f"Strong {category_name} subscription at {subscription_times:.1f}x")
        
        # Price positives
        issue_price_text = ipo_data.get('issue_price', '')
        issue_price = self._extract_max_price(issue_price_text)
        
        if issue_price and issue_price <= 100:
            positive_factors.append(f"Affordable issue price ₹{issue_price} for retail investors")
        elif issue_price and issue_price <= 200:
            positive_factors.append(f"Reasonable issue price ₹{issue_price}")
        
        # Size positives
        issue_size_text = ipo_data.get('issue_size', '')
        issue_size = self._extract_number(issue_size_text)
        
        if issue_size and issue_size <= 500:
            positive_factors.append(f"Small-medium issue size ₹{issue_size}Cr allows better price discovery")
        
        # Series positives
        series = ipo_data.get('series', '')
        if series == 'SME':
            positive_factors.append("SME IPO - historically better listing performance")
        
        # Score-based positives
        if scores.get('gmp_score', 0) > 70:
            positive_factors.append("Strong GMP analysis score indicates good market reception")
        
        if scores.get('subscription_score', 0) > 70:
            positive_factors.append("Excellent subscription metrics show strong demand")
        
        return positive_factors
    
    def _generate_investment_advice(self, recommendation: str, risk_level: str, 
                                  expected_gain: float) -> str:
        """Generate detailed investment advice"""
        
        advice_parts = []
        
        # Base recommendation advice
        if recommendation == 'BUY':
            advice_parts.append("🟢 RECOMMENDED FOR INVESTMENT")
            
            if risk_level == 'LOW':
                advice_parts.append("✅ Low risk profile suitable for conservative investors")
            elif risk_level == 'MEDIUM':
                advice_parts.append("⚠️ Medium risk - suitable for moderate risk appetite")
            else:
                advice_parts.append("⚠️ High risk - only for aggressive investors")
                
        elif recommendation == 'HOLD':
            advice_parts.append("🟡 NEUTRAL - PROCEED WITH CAUTION")
            advice_parts.append("📊 Mixed signals - thorough research recommended")
            
        else:  # AVOID
            advice_parts.append("🔴 NOT RECOMMENDED")
            advice_parts.append("❌ Multiple risk factors identified")
        
        # Expected return advice
        if expected_gain > 20:
            advice_parts.append(f"📈 High expected listing gain of {expected_gain}%")
        elif expected_gain > 10:
            advice_parts.append(f"📈 Good expected listing gain of {expected_gain}%")
        elif expected_gain > 0:
            advice_parts.append(f"📈 Modest expected gain of {expected_gain}%")
        else:
            advice_parts.append(f"📉 Potential loss risk of {abs(expected_gain)}%")
        
        # Risk management advice
        if risk_level == 'HIGH':
            advice_parts.append("🛡️ Use stop-loss at -5% if listing is negative")
            advice_parts.append("💡 Consider applying with minimum amount only")
        elif risk_level == 'MEDIUM':
            advice_parts.append("💡 Consider partial application or wait for better entry")
        
        # Timing advice
        advice_parts.append("⏰ Monitor subscription numbers and GMP trends")
        advice_parts.append("📱 Stay updated with company news and market conditions")
        
        return " | ".join(advice_parts)
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text"""
        if not text:
            return None
        
        try:
            # Remove currency and other symbols
            clean_text = re.sub(r'[₹,\s]', '', str(text).strip())
            
            # Extract number
            number_match = re.search(r'[\d.]+', clean_text)
            if number_match:
                return float(number_match.group())
            
            return None
            
        except Exception:
            return None
    
    def _extract_max_price(self, price_text: str) -> Optional[float]:
        """Extract maximum price from price range"""
        if not price_text:
            return None
        
        try:
            prices = re.findall(r'[\d.]+', price_text)
            if len(prices) >= 2:
                return float(prices[-1])  # Return max price
            elif len(prices) == 1:
                return float(prices[0])
            
            return None
            
        except Exception:
            return None

# Create prediction engine instance
ipo_prediction_engine = IPOPredictionEngine()