# app/controllers/gmp_controller.py
"""GMP Controller - Handles GMP analysis and prediction requests"""

from typing import Dict, Any, List
import logging
from datetime import datetime
from fastapi import HTTPException

from ..services.gmp_integration_service import gmp_integration_service
from ..services.nse_service import nse_service

logger = logging.getLogger(__name__)

class GMPController:
    """GMP Controller - Handles GMP-related HTTP requests"""
    
    def __init__(self):
        self.gmp_service = gmp_integration_service
        self.nse_service = nse_service
    
    async def analyze_current_ipos_with_gmp(self, save_data: bool = True) -> Dict[str, Any]:
        """Analyze current IPOs with GMP integration"""
        try:
            logger.info("Processing GMP analysis request for current IPOs")
            
            # Get current IPO data from NSE
            current_ipos = self.nse_service.fetch_current_ipos()
            if not current_ipos:
                raise HTTPException(
                    status_code=503,
                    detail="No current IPO data available from NSE"
                )
            
            # Get market status
            market_data = self.nse_service.fetch_market_status()
            
            # Perform GMP integration analysis
            analysis_result = self.gmp_service.analyze_current_ipos_with_gmp(
                nse_ipo_data=current_ipos,
                market_data=market_data
            )
            
            if not analysis_result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"GMP analysis failed: {analysis_result.get('error', 'Unknown error')}"
                )
            
            # Return comprehensive analysis
            return {
                'success': True,
                'message': f'Successfully analyzed {analysis_result["total_ipos_analyzed"]} IPOs with GMP data',
                'analysis_summary': analysis_result.get('summary', {}),
                'gmp_data_status': analysis_result.get('gmp_data_status', {}),
                'total_ipos_analyzed': analysis_result['total_ipos_analyzed'],
                'detailed_analyses': analysis_result.get('ipo_analyses', []),
                'analysis_timestamp': analysis_result.get('analysis_timestamp'),
                'saved_to_file': save_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'GMP_INTEGRATION_SERVICE'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - GMP analysis: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to perform GMP analysis: {str(e)}"
            )
    
    async def get_ipo_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Get specific IPO recommendation"""
        try:
            logger.info(f"Processing recommendation request for symbol: {symbol}")
            
            recommendation = self.gmp_service.get_ipo_recommendation(symbol)
            
            if not recommendation.get('success'):
                raise HTTPException(
                    status_code=404,
                    detail=f"No recommendation data found for {symbol}. Run analysis first."
                )
            
            return {
                'success': True,
                'message': f'Successfully retrieved recommendation for {symbol}',
                'symbol': symbol,
                'recommendation_data': recommendation,
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - get recommendation for {symbol}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get recommendation for {symbol}: {str(e)}"
            )
    
    async def get_top_recommendations(self, limit: int = 5) -> Dict[str, Any]:
        """Get top IPO recommendations"""
        try:
            logger.info(f"Processing top {limit} recommendations request")
            
            if limit < 1 or limit > 20:
                raise HTTPException(
                    status_code=400,
                    detail="Limit must be between 1 and 20"
                )
            
            top_recommendations = self.gmp_service.get_top_recommendations(limit)
            
            if not top_recommendations.get('success'):
                raise HTTPException(
                    status_code=404,
                    detail="No recommendation data available. Run analysis first."
                )
            
            return {
                'success': True,
                'message': f'Successfully retrieved top {limit} recommendations',
                'limit': limit,
                'total_analyzed': top_recommendations.get('total_analyzed', 0),
                'recommendations': top_recommendations.get('top_recommendations', []),
                'analysis_timestamp': top_recommendations.get('analysis_timestamp'),
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - get top recommendations: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get top recommendations: {str(e)}"
            )
    
    async def update_gmp_data(self) -> Dict[str, Any]:
        """Update GMP data from external sources"""
        try:
            logger.info("Processing GMP data update request")
            
            update_result = self.gmp_service.update_gmp_data()
            
            if not update_result.get('success'):
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to update GMP data: {update_result.get('message', 'Unknown error')}"
                )
            
            return {
                'success': True,
                'message': 'GMP data updated successfully',
                'update_details': {
                    'sources_scraped': update_result.get('sources_scraped', []),
                    'total_ipos': update_result.get('total_ipos', 0),
                    'saved_to_file': update_result.get('saved_to_file', False),
                    'scraping_errors': update_result.get('errors', [])
                },
                'data_timestamp': update_result.get('timestamp'),
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - update GMP data: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update GMP data: {str(e)}"
            )
    
    async def get_prediction_explanation(self, symbol: str) -> Dict[str, Any]:
        """Get detailed explanation of prediction methodology"""
        try:
            logger.info(f"Processing prediction explanation request for: {symbol}")
            
            # Get the recommendation first
            recommendation = self.gmp_service.get_ipo_recommendation(symbol)
            
            if not recommendation.get('success'):
                raise HTTPException(
                    status_code=404,
                    detail=f"No analysis data found for {symbol}"
                )
            
            rec_data = recommendation.get('recommendation', {})
            ipo_details = recommendation.get('ipo_details', {})
            gmp_data = recommendation.get('gmp_data', {})
            subscription_data = recommendation.get('subscription_data', {})
            
            # Create detailed explanation
            explanation = {
                'symbol': symbol,
                'company_name': ipo_details.get('company_name', ''),
                'analysis_methodology': {
                    'description': 'Our IPO prediction uses mathematical modeling with 5 key components',
                    'components': {
                        'gmp_analysis': {
                            'weight': '30%',
                            'description': 'Grey Market Premium analysis from multiple sources',
                            'score': rec_data.get('scores', {}).get('gmp_score', 0),
                            'factors': [
                                'Consensus GMP across sources',
                                'Data reliability score', 
                                'GMP trend analysis',
                                'Historical GMP accuracy'
                            ]
                        },
                        'subscription_analysis': {
                            'weight': '25%',
                            'description': 'Subscription pattern and demand analysis',
                            'score': rec_data.get('scores', {}).get('subscription_score', 0),
                            'factors': [
                                'Overall subscription ratio',
                                'Category-wise subscription',
                                'Retail vs institutional demand',
                                'Application quality'
                            ]
                        },
                        'fundamental_analysis': {
                            'weight': '20%',
                            'description': 'Company and issue fundamentals',
                            'score': rec_data.get('scores', {}).get('mathematical_score', 0),
                            'factors': [
                                'Issue price analysis',
                                'Issue size evaluation',
                                'Company track record',
                                'Valuation metrics'
                            ]
                        },
                        'market_conditions': {
                            'weight': '15%',
                            'description': 'Overall market environment',
                            'score': 50,  # Default market score
                            'factors': [
                                'Market sentiment',
                                'Sector performance',
                                'IPO market trends',
                                'Institutional appetite'
                            ]
                        },
                        'risk_assessment': {
                            'weight': '10%', 
                            'description': 'Risk factor evaluation',
                            'score': 100 - len(rec_data.get('risk_factors', [])) * 10,
                            'factors': [
                                'Price risk factors',
                                'Market timing risks',
                                'Company-specific risks',
                                'Liquidity concerns'
                            ]
                        }
                    }
                },
                'current_analysis': {
                    'final_score': rec_data.get('scores', {}).get('final_score', 0),
                    'recommendation': rec_data.get('recommendation', 'AVOID'),
                    'risk_level': rec_data.get('risk_level', 'HIGH'),
                    'confidence': rec_data.get('confidence_score', 0),
                    'expected_gain': rec_data.get('expected_listing_gain', 0),
                    'expected_price': rec_data.get('expected_listing_price', 0)
                },
                'data_sources': {
                    'nse_data': bool(ipo_details),
                    'gmp_sources': list(gmp_data.get('sources', {}).keys()) if gmp_data else [],
                    'subscription_data': bool(subscription_data),
                    'reliability_score': gmp_data.get('reliability_score', 0) if gmp_data else 0
                },
                'key_insights': {
                    'positive_factors': rec_data.get('positive_factors', []),
                    'risk_factors': rec_data.get('risk_factors', []),
                    'investment_advice': rec_data.get('investment_advice', ''),
                    'mathematical_reasoning': self._generate_mathematical_reasoning(rec_data)
                }
            }
            
            return {
                'success': True,
                'message': f'Prediction explanation generated for {symbol}',
                'explanation': explanation,
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - prediction explanation for {symbol}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate prediction explanation: {str(e)}"
            )
    
    async def get_market_analysis_summary(self) -> Dict[str, Any]:
        """Get overall market analysis summary"""
        try:
            logger.info("Processing market analysis summary request")
            
            # Get top recommendations
            top_recommendations = self.gmp_service.get_top_recommendations(10)
            
            if not top_recommendations.get('success'):
                raise HTTPException(
                    status_code=404,
                    detail="No analysis data available. Run analysis first."
                )
            
            recommendations = top_recommendations.get('top_recommendations', [])
            
            # Calculate market metrics
            market_metrics = self._calculate_market_metrics(recommendations)
            
            # Generate market insights
            market_insights = self._generate_market_insights(recommendations, market_metrics)
            
            return {
                'success': True,
                'message': 'Market analysis summary generated successfully',
                'market_metrics': market_metrics,
                'market_insights': market_insights,
                'top_opportunities': recommendations[:5],
                'analysis_timestamp': top_recommendations.get('analysis_timestamp'),
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - market analysis summary: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate market analysis summary: {str(e)}"
            )
    
    def _generate_mathematical_reasoning(self, rec_data: Dict) -> List[str]:
        """Generate mathematical reasoning for the prediction"""
        
        reasoning = []
        scores = rec_data.get('scores', {})
        
        # GMP reasoning
        gmp_score = scores.get('gmp_score', 0)
        if gmp_score > 70:
            reasoning.append(f"Strong GMP score ({gmp_score}/100) indicates positive market sentiment")
        elif gmp_score > 50:
            reasoning.append(f"Moderate GMP score ({gmp_score}/100) shows mixed market sentiment")
        else:
            reasoning.append(f"Low GMP score ({gmp_score}/100) indicates negative market sentiment")
        
        # Subscription reasoning
        sub_score = scores.get('subscription_score', 0)
        if sub_score > 70:
            reasoning.append(f"High subscription score ({sub_score}/100) shows strong investor demand")
        elif sub_score > 50:
            reasoning.append(f"Average subscription score ({sub_score}/100) indicates moderate demand")
        else:
            reasoning.append(f"Low subscription score ({sub_score}/100) shows weak investor interest")
        
        # Final score reasoning
        final_score = scores.get('final_score', 0)
        if final_score > 75:
            reasoning.append(f"Final weighted score ({final_score}/100) exceeds buy threshold of 75")
        elif final_score > 50:
            reasoning.append(f"Final weighted score ({final_score}/100) falls in hold range (50-74)")
        else:
            reasoning.append(f"Final weighted score ({final_score}/100) is below hold threshold of 50")
        
        return reasoning
    
    def _calculate_market_metrics(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Calculate overall market metrics"""
        
        if not recommendations:
            return {
                'total_ipos': 0,
                'buy_percentage': 0,
                'average_expected_gain': 0,
                'high_confidence_count': 0,
                'low_risk_count': 0
            }
        
        total_ipos = len(recommendations)
        buy_count = sum(1 for r in recommendations if r.get('recommendation') == 'BUY')
        high_confidence_count = sum(1 for r in recommendations if r.get('confidence_score', 0) > 80)
        low_risk_count = sum(1 for r in recommendations if r.get('risk_level') == 'LOW')
        
        expected_gains = [r.get('expected_listing_gain', 0) for r in recommendations]
        avg_expected_gain = sum(expected_gains) / len(expected_gains) if expected_gains else 0
        
        return {
            'total_ipos': total_ipos,
            'buy_percentage': round((buy_count / total_ipos) * 100, 1),
            'average_expected_gain': round(avg_expected_gain, 2),
            'high_confidence_count': high_confidence_count,
            'low_risk_count': low_risk_count,
            'high_confidence_percentage': round((high_confidence_count / total_ipos) * 100, 1),
            'low_risk_percentage': round((low_risk_count / total_ipos) * 100, 1)
        }
    
    def _generate_market_insights(self, recommendations: List[Dict], 
                                metrics: Dict[str, Any]) -> List[str]:
        """Generate market insights"""
        
        insights = []
        
        # Overall market sentiment
        buy_percentage = metrics.get('buy_percentage', 0)
        if buy_percentage > 60:
            insights.append(f"🟢 Strong IPO market with {buy_percentage}% of IPOs recommended as BUY")
        elif buy_percentage > 30:
            insights.append(f"🟡 Mixed IPO market with {buy_percentage}% BUY recommendations")
        else:
            insights.append(f"🔴 Weak IPO market with only {buy_percentage}% BUY recommendations")
        
        # Expected gains
        avg_gain = metrics.get('average_expected_gain', 0)
        if avg_gain > 15:
            insights.append(f"📈 High expected returns averaging {avg_gain}% listing gains")
        elif avg_gain > 5:
            insights.append(f"📊 Moderate expected returns averaging {avg_gain}% listing gains")
        else:
            insights.append(f"📉 Low expected returns averaging {avg_gain}% listing gains")
        
        # Risk assessment
        low_risk_percentage = metrics.get('low_risk_percentage', 0)
        if low_risk_percentage > 40:
            insights.append(f"🛡️ Safe market environment with {low_risk_percentage}% low-risk IPOs")
        elif low_risk_percentage > 20:
            insights.append(f"⚖️ Balanced risk environment with {low_risk_percentage}% low-risk IPOs")
        else:
            insights.append(f"⚠️ High-risk market with only {low_risk_percentage}% low-risk IPOs")
        
        # Confidence levels
        high_confidence_percentage = metrics.get('high_confidence_percentage', 0)
        if high_confidence_percentage > 50:
            insights.append(f"✅ High prediction confidence with {high_confidence_percentage}% reliable forecasts")
        else:
            insights.append(f"🔍 Mixed prediction confidence with {high_confidence_percentage}% high-confidence forecasts")
        
        return insights

# Create controller instance
gmp_controller = GMPController()