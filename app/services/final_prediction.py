# app/services/final_prediction.py - COMPLETE INTELLIGENT SYSTEM

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FinalPredictionService:
    """
    Intelligent IPO Final Prediction System
    Combines GMP, Math, and AI predictions with smart weighting
    """
    
    # Weight configurations based on data availability
    WEIGHTS_WITH_GMP = {
        'gmp': 0.50,    # 50% - Real market sentiment is strongest
        'math': 0.30,   # 30% - Quantitative validation
        'ai': 0.20      # 20% - Fundamental safety check
    }
    
    WEIGHTS_WITHOUT_GMP = {
        'gmp': 0.0,     # 0% - Not available
        'math': 0.60,   # 60% - Primary quantitative source
        'ai': 0.40      # 40% - Qualitative analysis
    }
    
    # Recommendation mapping
    REC_SCORES = {
        'STRONG_BUY': 100,
        'BUY': 75,
        'MODERATE_BUY': 60,
        'HOLD': 50,
        'AVOID': 25,
        'STRONG_AVOID': 0,
        'INSUFFICIENT_DATA': 0,
        'NO_DATA': 0
    }
    
    # Risk mapping
    RISK_SCORES = {
        'LOW': 100,
        'MEDIUM-LOW': 75,
        'MEDIUM': 50,
        'MEDIUM-HIGH': 35,
        'HIGH': 20,
        'VERY_HIGH': 0
    }
    
    # Confidence mapping
    CONFIDENCE_SCORES = {
        'VERY_HIGH': 100,
        'HIGH': 80,
        'MEDIUM': 60,
        'LOW': 40,
        'VERY_LOW': 20
    }
    
    def combine_predictions(self, 
                           gmp_pred: Dict, 
                           math_pred: Dict, 
                           ai_pred: Dict,
                           ipo_data: Dict) -> Dict:
        """
        Main function: Intelligently combine all predictions
        """
        try:
            symbol = ipo_data.get('symbol', 'UNKNOWN')
            company_name = ipo_data.get('company_name', '')
            
            logger.info(f"🎯 Generating final prediction for {symbol}")
            
            # Step 1: Extract and normalize all predictions
            gmp_analysis = self._analyze_gmp_prediction(gmp_pred)
            math_analysis = self._analyze_math_prediction(math_pred)
            ai_analysis = self._analyze_ai_prediction(ai_pred)
            
            # Step 2: Determine weighting strategy
            has_gmp = gmp_analysis['has_data']
            weights = self.WEIGHTS_WITH_GMP if has_gmp else self.WEIGHTS_WITHOUT_GMP
            
            logger.info(f"Using weights: GMP={weights['gmp']}, Math={weights['math']}, AI={weights['ai']}")
            
            # Step 3: Calculate weighted metrics
            weighted_gain = self._calculate_weighted_gain(
                gmp_analysis, math_analysis, ai_analysis, weights
            )
            
            # Step 4: Generate final recommendation with consensus analysis
            final_recommendation, consensus_strength = self._generate_final_recommendation(
                gmp_analysis, math_analysis, ai_analysis, weights
            )
            
            # Step 5: Calculate overall risk and confidence
            overall_risk = self._calculate_overall_risk(
                gmp_analysis, math_analysis, ai_analysis, weights
            )
            
            overall_confidence = self._calculate_overall_confidence(
                gmp_analysis, math_analysis, ai_analysis, weights, consensus_strength
            )
            
            # Step 6: Calculate expected listing price
            issue_price = self._extract_price(ipo_data.get('issue_price', ''))
            expected_listing = issue_price * (1 + weighted_gain/100) if issue_price else 0
            
            # Step 7: Generate detailed reasoning
            reasoning = self._generate_detailed_reasoning(
                gmp_analysis, math_analysis, ai_analysis, 
                final_recommendation, consensus_strength, has_gmp
            )
            
            # Step 8: Investment advice based on risk profile
            investment_advice = self._generate_investment_advice(
                final_recommendation, overall_risk, weighted_gain, consensus_strength
            )
            
            # Step 9: Build final prediction response
            final_prediction = {
                'symbol': symbol,
                'company_name': company_name,
                'timestamp': datetime.now().isoformat(),
                'prediction_date': datetime.now().strftime('%Y-%m-%d'),
                
                # Main Prediction
                'final_recommendation': final_recommendation,
                'consensus_strength': consensus_strength,
                'expected_gain_percent': round(weighted_gain, 2),
                'expected_listing_price': round(expected_listing, 2),
                'issue_price': issue_price,
                'overall_risk_level': overall_risk,
                'overall_confidence': overall_confidence,
                
                # Detailed Analysis
                'reasoning': reasoning,
                'investment_advice': investment_advice,
                
                # Individual Source Analysis
                'source_predictions': {
                    'gmp': {
                        'available': gmp_analysis['has_data'],
                        'recommendation': gmp_analysis['recommendation'],
                        'expected_gain': gmp_analysis['gain'],
                        'listing_gain_text': gmp_pred.get('listing_gain_percent', 'N/A'),
                        'weight_used': weights['gmp'],
                        'reliability': 'HIGH' if has_gmp else 'N/A'
                    },
                    'math': {
                        'recommendation': math_analysis['recommendation'],
                        'expected_gain': math_analysis['gain'],
                        'confidence': math_analysis['confidence'],
                        'risk': math_analysis['risk'],
                        'score': math_analysis['score'],
                        'subscription_times': math_pred.get('subscription_analysis', {}).get('total_subscription', 0),
                        'weight_used': weights['math'],
                        'reliability': 'MEDIUM-HIGH'
                    },
                    'ai': {
                        'recommendation': ai_analysis['recommendation'],
                        'expected_gain': ai_analysis['gain'],
                        'confidence': ai_analysis['confidence'],
                        'risk': ai_analysis['risk'],
                        'key_factors': ai_pred.get('key_factors', [])[:3],
                        'sector_outlook': ai_pred.get('sector_outlook', ''),
                        'weight_used': weights['ai'],
                        'reliability': 'MEDIUM'
                    }
                },
                
                # IPO Details
                'ipo_details': {
                    'issue_price_range': ipo_data.get('issue_price', ''),
                    'issue_size': ipo_data.get('issue_size', ''),
                    'issue_start': ipo_data.get('issue_start_date', ''),
                    'issue_end': ipo_data.get('issue_end_date', ''),
                    'subscription': ipo_data.get('subscription_times', 0),
                    'status': ipo_data.get('status', ''),
                    'series': ipo_data.get('series', '')
                },
                
                # Metadata
                'weights_used': weights,
                'has_gmp_data': has_gmp,
                'prediction_methodology': 'WEIGHTED_CONSENSUS_V2'
            }
            
            logger.info(f"✅ Final prediction: {final_recommendation} ({consensus_strength})")
            
            return final_prediction
            
        except Exception as e:
            logger.error(f"Final prediction error: {e}", exc_info=True)
            return self._error_prediction(ipo_data, str(e))
    
    def _analyze_gmp_prediction(self, gmp_pred: Dict) -> Dict:
        """Analyze and normalize GMP prediction"""
        try:
            has_data = gmp_pred.get('has_data', False) or gmp_pred.get('found', False)
            
            if not has_data:
                return {
                    'has_data': False,
                    'gain': 0,
                    'recommendation': 'NO_DATA',
                    'score': 0
                }
            
            # Extract gain from GMP
            gain = gmp_pred.get('expected_gain_percent', 0)
            if gain == 0:
                # Try listing_gain
                gain = gmp_pred.get('listing_gain', 0)
            
            # Determine recommendation from GMP gain
            if gain >= 20:
                rec = 'STRONG_BUY'
            elif gain >= 10:
                rec = 'BUY'
            elif gain >= 5:
                rec = 'MODERATE_BUY'
            elif gain >= 0:
                rec = 'HOLD'
            else:
                rec = 'AVOID'
            
            return {
                'has_data': True,
                'gain': float(gain),
                'recommendation': rec,
                'score': self.REC_SCORES.get(rec, 50)
            }
            
        except Exception as e:
            logger.error(f"GMP analysis error: {e}")
            return {'has_data': False, 'gain': 0, 'recommendation': 'NO_DATA', 'score': 0}
    
    def _analyze_math_prediction(self, math_pred: Dict) -> Dict:
        """Analyze and normalize Math prediction"""
        try:
            prediction = math_pred.get('prediction', {})
            
            gain = prediction.get('expected_gain_percent', 0)
            rec = prediction.get('recommendation', 'HOLD')
            confidence = prediction.get('confidence', 'MEDIUM')
            risk = prediction.get('risk_level', 'MEDIUM')
            score = prediction.get('final_score', 50)
            
            return {
                'gain': float(gain),
                'recommendation': rec,
                'confidence': confidence,
                'risk': risk,
                'score': float(score)
            }
            
        except Exception as e:
            logger.error(f"Math analysis error: {e}")
            return {
                'gain': 0,
                'recommendation': 'INSUFFICIENT_DATA',
                'confidence': 'LOW',
                'risk': 'HIGH',
                'score': 0
            }
    
    def _analyze_ai_prediction(self, ai_pred: Dict) -> Dict:
        """Analyze and normalize AI prediction"""
        try:
            gain = ai_pred.get('expected_gain_percent', 0)
            rec = ai_pred.get('recommendation', 'HOLD')
            confidence = ai_pred.get('confidence', 'MEDIUM')
            risk = ai_pred.get('risk_level', 'MEDIUM')
            
            return {
                'gain': float(gain),
                'recommendation': rec,
                'confidence': confidence,
                'risk': risk,
                'reasoning': ai_pred.get('reasoning', '')
            }
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {
                'gain': 0,
                'recommendation': 'INSUFFICIENT_DATA',
                'confidence': 'LOW',
                'risk': 'HIGH',
                'reasoning': 'Analysis failed'
            }
    
    def _calculate_weighted_gain(self, gmp_analysis: Dict, math_analysis: Dict, 
                                 ai_analysis: Dict, weights: Dict) -> float:
        """Calculate weighted average expected gain"""
        total_gain = (
            gmp_analysis['gain'] * weights['gmp'] +
            math_analysis['gain'] * weights['math'] +
            ai_analysis['gain'] * weights['ai']
        )
        return total_gain
    
    def _generate_final_recommendation(self, gmp_analysis: Dict, math_analysis: Dict,
                                       ai_analysis: Dict, weights: Dict) -> Tuple[str, str]:
        """
        Generate final recommendation with consensus analysis
        Returns: (recommendation, consensus_strength)
        """
        recommendations = []
        rec_weights = []
        
        # Collect recommendations with weights
        if gmp_analysis['has_data']:
            recommendations.append(gmp_analysis['recommendation'])
            rec_weights.append(weights['gmp'])
        
        recommendations.append(math_analysis['recommendation'])
        rec_weights.append(weights['math'])
        
        recommendations.append(ai_analysis['recommendation'])
        rec_weights.append(weights['ai'])
        
        # Count BUY/AVOID signals
        buy_signals = sum(1 for r in recommendations if 'BUY' in r)
        avoid_signals = sum(1 for r in recommendations if 'AVOID' in r)
        total_signals = len(recommendations)
        
        # Weighted score calculation
        weighted_score = (
            self.REC_SCORES.get(gmp_analysis['recommendation'], 0) * weights['gmp'] +
            self.REC_SCORES.get(math_analysis['recommendation'], 50) * weights['math'] +
            self.REC_SCORES.get(ai_analysis['recommendation'], 50) * weights['ai']
        )
        
        # Determine consensus strength
        if buy_signals == total_signals:
            consensus = "UNANIMOUS"
        elif buy_signals >= total_signals * 0.67:
            consensus = "STRONG"
        elif buy_signals > avoid_signals:
            consensus = "MODERATE"
        elif avoid_signals >= total_signals * 0.67:
            consensus = "STRONG_NEGATIVE"
        else:
            consensus = "MIXED"
        
        # Final recommendation based on weighted score and consensus
        if weighted_score >= 80 and buy_signals >= 2:
            final_rec = 'STRONG_BUY'
        elif weighted_score >= 65 and consensus in ['UNANIMOUS', 'STRONG']:
            final_rec = 'BUY'
        elif weighted_score >= 55:
            final_rec = 'MODERATE_BUY'
        elif weighted_score >= 45:
            final_rec = 'HOLD'
        elif avoid_signals >= 2:
            final_rec = 'AVOID'
        else:
            final_rec = 'HOLD'
        
        logger.info(f"Recommendation logic: Score={weighted_score:.1f}, Buy={buy_signals}/{total_signals}, Consensus={consensus}")
        
        return final_rec, consensus
    
    def _calculate_overall_risk(self, gmp_analysis: Dict, math_analysis: Dict,
                                ai_analysis: Dict, weights: Dict) -> str:
        """Calculate overall risk level"""
        risk_score = (
            self.RISK_SCORES.get(math_analysis['risk'], 50) * weights['math'] +
            self.RISK_SCORES.get(ai_analysis['risk'], 50) * weights['ai']
        )
        
        # GMP presence reduces risk
        if gmp_analysis['has_data'] and gmp_analysis['gain'] > 10:
            risk_score += 15
        
        if risk_score >= 80:
            return 'LOW'
        elif risk_score >= 60:
            return 'MEDIUM-LOW'
        elif risk_score >= 40:
            return 'MEDIUM'
        elif risk_score >= 25:
            return 'MEDIUM-HIGH'
        else:
            return 'HIGH'
    
    def _calculate_overall_confidence(self, gmp_analysis: Dict, math_analysis: Dict,
                                     ai_analysis: Dict, weights: Dict, 
                                     consensus: str) -> str:
        """Calculate overall confidence"""
        conf_score = (
            self.CONFIDENCE_SCORES.get(math_analysis['confidence'], 50) * weights['math'] +
            self.CONFIDENCE_SCORES.get(ai_analysis['confidence'], 50) * weights['ai']
        )
        
        # GMP increases confidence
        if gmp_analysis['has_data']:
            conf_score += 20
        
        # Consensus affects confidence
        if consensus == 'UNANIMOUS':
            conf_score += 15
        elif consensus == 'STRONG':
            conf_score += 10
        elif consensus == 'MIXED':
            conf_score -= 15
        
        conf_score = min(100, conf_score)
        
        if conf_score >= 85:
            return 'VERY_HIGH'
        elif conf_score >= 70:
            return 'HIGH'
        elif conf_score >= 50:
            return 'MEDIUM'
        elif conf_score >= 30:
            return 'LOW'
        else:
            return 'VERY_LOW'
    
    def _generate_detailed_reasoning(self, gmp_analysis: Dict, math_analysis: Dict,
                                    ai_analysis: Dict, final_rec: str, 
                                    consensus: str, has_gmp: bool) -> str:
        """Generate human-readable reasoning"""
        reasoning_parts = []
        
        # Consensus analysis
        if consensus == 'UNANIMOUS':
            reasoning_parts.append("All prediction models unanimously agree")
        elif consensus == 'STRONG':
            reasoning_parts.append("Strong consensus across prediction models")
        elif consensus == 'MODERATE':
            reasoning_parts.append("Moderate agreement between models with some divergence")
        elif consensus == 'MIXED':
            reasoning_parts.append("Mixed signals - proceed with caution")
        else:
            reasoning_parts.append("Negative consensus - high risk identified")
        
        # GMP analysis
        if has_gmp:
            if gmp_analysis['gain'] >= 15:
                reasoning_parts.append(f"Strong grey market premium of {gmp_analysis['gain']:.1f}% indicates high demand")
            elif gmp_analysis['gain'] >= 5:
                reasoning_parts.append(f"Positive grey market premium of {gmp_analysis['gain']:.1f}%")
            elif gmp_analysis['gain'] < 0:
                reasoning_parts.append(f"Negative GMP of {gmp_analysis['gain']:.1f}% is concerning")
        else:
            reasoning_parts.append("No grey market data available - relying on quantitative analysis")
        
        # Math analysis
        if math_analysis['score'] >= 70:
            reasoning_parts.append(f"Strong subscription patterns support positive listing")
        elif math_analysis['score'] < 30:
            reasoning_parts.append(f"Weak subscription data suggests caution")
        
        # AI insights
        if ai_analysis['recommendation'] in ['STRONG_BUY', 'BUY']:
            reasoning_parts.append("Fundamentals and sector outlook are favorable")
        elif ai_analysis['recommendation'] == 'AVOID':
            reasoning_parts.append("AI analysis identified fundamental concerns")
        
        return ". ".join(reasoning_parts) + "."
    
    def _generate_investment_advice(self, recommendation: str, risk: str, 
                                   gain: float, consensus: str) -> Dict:
        """Generate actionable investment advice"""
        advice = {
            'action': '',
            'allocation': '',
            'holding_period': '',
            'exit_strategy': '',
            'caution_points': []
        }
        
        if recommendation == 'STRONG_BUY':
            advice['action'] = 'Apply with full allocation'
            advice['allocation'] = 'Up to 100% of IPO budget'
            advice['holding_period'] = 'Hold for listing day gains, review for long-term'
            advice['exit_strategy'] = 'Book 50% profits on listing, hold balance'
            
        elif recommendation == 'BUY':
            advice['action'] = 'Apply with high allocation'
            advice['allocation'] = '60-80% of IPO budget'
            advice['holding_period'] = 'Short to medium term (listing + 1-3 months)'
            advice['exit_strategy'] = 'Book partial profits on listing if gains > 20%'
            
        elif recommendation == 'MODERATE_BUY':
            advice['action'] = 'Apply with moderate allocation'
            advice['allocation'] = '30-50% of IPO budget'
            advice['holding_period'] = 'Review post-listing performance'
            advice['exit_strategy'] = 'Exit if listing gains < 5%'
            advice['caution_points'].append('Mixed signals - monitor closely')
            
        elif recommendation == 'HOLD':
            advice['action'] = 'Consider applying only if surplus funds available'
            advice['allocation'] = '10-20% of IPO budget'
            advice['holding_period'] = 'Immediate exit on listing'
            advice['exit_strategy'] = 'Exit immediately on any positive gain'
            advice['caution_points'].append('Uncertain outlook')
            
        else:  # AVOID
            advice['action'] = 'Skip this IPO'
            advice['allocation'] = '0%'
            advice['holding_period'] = 'N/A'
            advice['exit_strategy'] = 'N/A'
            advice['caution_points'].append('High risk identified')
        
        # Add risk-based cautions
        if risk in ['HIGH', 'MEDIUM-HIGH']:
            advice['caution_points'].append(f'{risk} risk level - use stop loss')
        
        if consensus == 'MIXED':
            advice['caution_points'].append('Conflicting predictions - proceed carefully')
        
        return advice
    
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
    
    def _error_prediction(self, ipo_data: Dict, error: str) -> Dict:
        """Generate error prediction"""
        return {
            'symbol': ipo_data.get('symbol', 'UNKNOWN'),
            'company_name': ipo_data.get('company_name', ''),
            'final_recommendation': 'INSUFFICIENT_DATA',
            'error': error,
            'message': 'Unable to generate final prediction due to data error',
            'timestamp': datetime.now().isoformat()
        }

# Create service instance
final_prediction_service = FinalPredictionService()