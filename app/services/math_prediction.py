# app/services/math_prediction.py

import logging
import math
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MathPredictionService:
    """Advanced Mathematical Prediction Service - Research Based Models"""
    
    # Research-backed weight coefficients
    WEIGHTS = {
        'qib': 0.65,      # QIB has 65% predictive power
        'nii': 0.20,      # NII has 20% weight
        'retail': 0.15    # Retail has 15% weight
    }
    
    # Subscription to gain mapping (from research document)
    GAIN_THRESHOLDS = [
        (1.0, -10, 5, 0.65),       # < 1x: -10% to +5%, P(Loss) = 65%
        (5.0, 5, 25, 0.70),        # 1-5x: +5% to +25%
        (20.0, 20, 60, 0.80),      # 5-20x: +20% to +60%
        (50.0, 45, 120, 0.85),     # 20-50x: +45% to +120%
        (float('inf'), 80, 200, 0.75)  # >50x: +80% to +200%
    ]
    
    def predict(self, ipo_data: Dict, subscription_data: Optional[Dict] = None) -> Dict:
        """
        Main prediction function - generates complete analysis
        
        Args:
            ipo_data: IPO details from NSE
            subscription_data: Subscription details with categories
        
        Returns:
            Complete prediction with all metrics
        """
        try:
            symbol = ipo_data.get('symbol', 'UNKNOWN')
            
            # Extract subscription metrics
            sub_metrics = self._extract_subscription_metrics(subscription_data)
            total_sub = sub_metrics['total']
            
            # Calculate weighted subscription score
            weighted_score = self._calculate_weighted_subscription(sub_metrics)
            
            # Calculate expected gain using research formula
            base_gain = self._calculate_expected_gain(sub_metrics)
            
            # Apply undersubscription penalty if needed
            adjusted_gain = self._apply_undersubscription_penalty(base_gain, total_sub)
            
            # Calculate risk and confidence
            risk_level = self._calculate_risk_level(total_sub, sub_metrics['qib'])
            confidence = self._calculate_confidence(total_sub, sub_metrics['qib'])
            
            # Generate recommendation
            recommendation = self._generate_recommendation(adjusted_gain, risk_level, total_sub)
            
            # Calculate final score (0-100)
            final_score = self._calculate_final_score(weighted_score, adjusted_gain, total_sub)
            
            # Get gain range based on subscription
            gain_range = self._get_gain_range(total_sub)
            
            # Calculate probability metrics
            prob_positive = self._calculate_probability_positive(total_sub)
            
            # Extract issue price and calculate listing price prediction
            listing_prediction = self._calculate_listing_price(ipo_data, adjusted_gain, gain_range)
            
            return {
                'symbol': symbol,
                'company_name': ipo_data.get('company_name', ''),
                'source': 'MATH_RESEARCH_MODEL',
                'prediction': {
                    'expected_gain_percent': round(adjusted_gain, 2),
                    'expected_gain_rupees': listing_prediction['gain_rupees'],
                    'listing_price_prediction': listing_prediction['listing_price'],
                    'gain_range': gain_range,
                    'gain_range_rupees': listing_prediction['gain_range_rupees'],
                    'final_score': round(final_score, 2),
                    'recommendation': recommendation,
                    'confidence': confidence,
                    'risk_level': risk_level
                },
                'subscription_analysis': {
                    'total_subscription': round(total_sub, 2),
                    'qib_subscription': round(sub_metrics['qib'], 2),
                    'nii_subscription': round(sub_metrics['nii'], 2),
                    'retail_subscription': round(sub_metrics['retail'], 2),
                    'weighted_score': round(weighted_score, 2)
                },
                'probability_metrics': {
                    'prob_positive_return': round(prob_positive * 100, 2),
                    'prob_loss': round((1 - prob_positive) * 100, 2)
                },
                'model_details': {
                    'base_gain_before_penalty': round(base_gain, 2),
                    'undersubscription_penalty': round(base_gain - adjusted_gain, 2),
                    'formula': 'Rock_Winner_Curse_Adapted',
                    'weights': self.WEIGHTS
                },
                'ipo_details': {
                    'issue_price': ipo_data.get('issue_price', ''),
                    'issue_size': ipo_data.get('issue_size', ''),
                    'series': ipo_data.get('series', ''),
                    'status': ipo_data.get('status', '')
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Prediction error for {ipo_data.get('symbol')}: {e}")
            return self._default_prediction(ipo_data)
    
    def _extract_subscription_metrics(self, subscription_data: Optional[Dict]) -> Dict:
        """Extract clean subscription metrics from NSE data"""
        default = {'total': 0, 'qib': 0, 'nii': 0, 'retail': 0}
        
        # Check if subscription_data exists and has the required structure
        if not subscription_data:
            logger.warning("No subscription data provided")
            return default
        
        # subscription_data is already the symbol-specific data with 'categories' key
        if 'categories' not in subscription_data:
            logger.warning("No categories found in subscription data")
            return default
        
        categories = subscription_data['categories']
        total_sub = subscription_data.get('total_subscription', 0)
        
        # Extract QIB subscription
        qib = categories.get('Qualified Institutional Buyers(QIBs)', {}).get('subscription_times', 0)
        
        # Extract NII subscription
        nii = categories.get('Non Institutional Investors', {}).get('subscription_times', 0)
        
        # Extract Retail subscription
        retail = categories.get('Retail Individual Investors(RIIs)', {}).get('subscription_times', 0)
        
        logger.info(f"Extracted metrics - Total: {total_sub}, QIB: {qib}, NII: {nii}, Retail: {retail}")
        
        return {
            'total': total_sub,
            'qib': qib,
            'nii': nii,
            'retail': retail
        }
    
    def _calculate_weighted_subscription(self, metrics: Dict) -> float:
        """
        Weighted subscription score using research formula:
        Weighted = 0.65×QIB + 0.20×NII + 0.15×Retail
        """
        return (
            metrics['qib'] * self.WEIGHTS['qib'] +
            metrics['nii'] * self.WEIGHTS['nii'] +
            metrics['retail'] * self.WEIGHTS['retail']
        )
    
    def _calculate_expected_gain(self, metrics: Dict) -> float:
        """
        Expected gain using research formula:
        Expected Gain = 12.5 × log(Subscription) + Category_Weighted_Component
        """
        total_sub = metrics['total']
        
        if total_sub <= 0:
            return -10.0
        
        # Primary formula: 12.5 × log(Subscription Ratio)
        log_component = 12.5 * math.log10(max(total_sub, 0.01))
        
        # Category-weighted prediction (research formula)
        category_component = (
            metrics['qib'] * 15.2 * self.WEIGHTS['qib'] +
            metrics['nii'] * 12.8 * self.WEIGHTS['nii'] +
            metrics['retail'] * 8.4 * self.WEIGHTS['retail']
        )
        
        # Combine both methods (average for stability)
        expected_gain = (log_component + category_component) / 2
        
        return expected_gain
    
    def _apply_undersubscription_penalty(self, base_gain: float, subscription: float) -> float:
        """
        Apply penalty for undersubscribed IPOs:
        Penalty Factor = max(0, 1 - Subscription)²
        Adjusted Return = Base × (1 - Penalty)
        """
        if subscription >= 1.0:
            return base_gain
        
        penalty_factor = max(0, 1 - subscription) ** 2
        adjusted_gain = base_gain * (1 - penalty_factor)
        
        return adjusted_gain
    
    def _calculate_risk_level(self, total_sub: float, qib_sub: float) -> str:
        """Calculate risk level based on subscription patterns"""
        if total_sub < 1.0:
            return 'HIGH'
        elif total_sub < 5.0:
            return 'MEDIUM' if qib_sub >= 2.0 else 'MEDIUM-HIGH'
        elif total_sub < 20.0:
            return 'MEDIUM-LOW'
        else:
            return 'LOW'
    
    def _calculate_confidence(self, total_sub: float, qib_sub: float) -> str:
        """Calculate prediction confidence"""
        if qib_sub >= 10.0 and total_sub >= 20.0:
            return 'VERY_HIGH'
        elif qib_sub >= 5.0 and total_sub >= 10.0:
            return 'HIGH'
        elif qib_sub >= 1.0 and total_sub >= 3.0:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_recommendation(self, expected_gain: float, risk: str, total_sub: float) -> str:
        """Generate investment recommendation"""
        if total_sub < 1.0:
            return 'AVOID'
        
        if expected_gain >= 40 and risk in ['LOW', 'MEDIUM-LOW']:
            return 'STRONG_BUY'
        elif expected_gain >= 20 and risk != 'HIGH':
            return 'BUY'
        elif expected_gain >= 10:
            return 'MODERATE_BUY'
        elif expected_gain >= 5:
            return 'HOLD'
        else:
            return 'AVOID'
    
    def _calculate_probability_positive(self, subscription: float) -> float:
        """Calculate probability of positive return (research data)"""
        for threshold, _, _, prob in self.GAIN_THRESHOLDS:
            if subscription < threshold:
                return prob
        return 0.75
    
    def _get_gain_range(self, subscription: float) -> Dict:
        """Get expected gain range based on subscription level"""
        for threshold, min_gain, max_gain, prob in self.GAIN_THRESHOLDS:
            if subscription < threshold:
                return {
                    'min': min_gain,
                    'max': max_gain,
                    'probability': prob
                }
        return {'min': -10, 'max': 5, 'probability': 0.65}
    
    def _calculate_final_score(self, weighted_sub: float, expected_gain: float, total_sub: float) -> float:
        """
        Calculate final score (0-100 scale)
        Combines subscription strength and expected gain
        """
        # Subscription component (0-100)
        sub_score = min(100, weighted_sub * 15)
        
        # Gain component (normalized to 0-100)
        gain_score = min(100, max(0, (expected_gain + 20) * 2))
        
        # Undersubscription penalty
        penalty = 0
        if total_sub < 1.0:
            penalty = (1 - total_sub) * 40
        
        # Final weighted score
        final = (sub_score * 0.6 + gain_score * 0.4) - penalty
        
        return max(0, min(100, final))
    
    def _calculate_listing_price(self, ipo_data: Dict, gain_percent: float, gain_range: Dict) -> Dict:
        """
        Calculate listing price prediction in rupees (like GMP)
        
        Returns absolute rupee values for listing price prediction
        """
        import re
        
        issue_price_text = ipo_data.get('issue_price', '')
        
        # Extract price from text like "Rs.181 to Rs.191"
        prices = re.findall(r'[\d.]+', issue_price_text)
        
        if not prices:
            return {
                'issue_price': 0,
                'listing_price': 0,
                'gain_rupees': 0,
                'gain_range_rupees': {'min': 0, 'max': 0}
            }
        
        # Use upper price (listing pe mostly upper price hi consider hota hai)
        issue_price = float(prices[-1])
        
        # Calculate listing price based on expected gain
        gain_rupees = round((issue_price * gain_percent) / 100, 2)
        listing_price = round(issue_price + gain_rupees, 2)
        
        # Calculate gain range in rupees
        min_gain_rupees = round((issue_price * gain_range['min']) / 100, 2)
        max_gain_rupees = round((issue_price * gain_range['max']) / 100, 2)
        
        return {
            'issue_price': issue_price,
            'listing_price': listing_price,
            'gain_rupees': gain_rupees,
            'gain_range_rupees': {
                'min': min_gain_rupees,
                'max': max_gain_rupees
            }
        }
    
    def _default_prediction(self, ipo_data: Dict) -> Dict:
        """Default prediction when data is insufficient"""
        return {
            'symbol': ipo_data.get('symbol', 'UNKNOWN'),
            'company_name': ipo_data.get('company_name', ''),
            'source': 'MATH_RESEARCH_MODEL',
            'prediction': {
                'expected_gain_percent': 0.0,
                'gain_range': {'min': -10, 'max': 5, 'probability': 0.5},
                'final_score': 50.0,
                'recommendation': 'INSUFFICIENT_DATA',
                'confidence': 'LOW',
                'risk_level': 'UNKNOWN'
            },
            'error': 'Insufficient subscription data',
            'timestamp': datetime.now().isoformat()
        }

math_prediction_service = MathPredictionService()