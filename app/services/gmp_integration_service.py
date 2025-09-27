# app/services/gmp_integration_service.py
"""GMP Integration Service - Combines NSE data with GMP analysis"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .gmp_scraper import gmp_scraper
from .ipo_prediction_engine import ipo_prediction_engine
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class GMPIntegrationService:
    """Service to integrate GMP data with NSE IPO data"""
    
    def __init__(self):
        self.gmp_scraper = gmp_scraper
        self.prediction_engine = ipo_prediction_engine
        self.file_storage = file_storage
    
    def analyze_current_ipos_with_gmp(self, nse_ipo_data: List[Dict], 
                                     market_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Analyze current IPOs with GMP data and predictions
        
        Args:
            nse_ipo_data: Current IPO data from NSE
            market_data: Market status data
            
        Returns:
            Comprehensive analysis with predictions
        """
        
        logger.info("Starting GMP integration analysis for current IPOs...")
        
        try:
            # Scrape latest GMP data
            gmp_data = self.gmp_scraper.scrape_gmp_data()
            
            # Load subscription data from local files
            subscription_data = self._load_subscription_data()
            
            # Analyze each IPO
            ipo_analyses = []
            
            for ipo in nse_ipo_data:
                symbol = ipo.get('symbol', '')
                company_name = ipo.get('company_name', '')
                
                logger.info(f"Analyzing {symbol} - {company_name}")
                
                # Find matching GMP data
                matching_gmp = self._find_matching_gmp(symbol, company_name, gmp_data['data'])
                
                # Find subscription data
                matching_subscription = subscription_data.get(symbol)
                
                # Generate prediction (without GMP data - engine predicts independently)
                prediction = self.prediction_engine.predict_ipo_performance(
                    ipo_data=ipo,
                    subscription_data=matching_subscription,
                    market_data={'data': market_data} if market_data else None
                )
                
                # Compile analysis
                analysis = {
                    'ipo_details': ipo,
                    'gmp_data': matching_gmp,
                    'subscription_data': matching_subscription,
                    'prediction': {
                        'recommendation': prediction.recommendation,
                        'risk_level': prediction.risk_level,
                        'confidence_score': prediction.confidence_score,
                        'expected_listing_gain': prediction.expected_listing_gain,
                        'expected_listing_price': prediction.expected_listing_price,
                        'risk_factors': prediction.risk_factors,
                        'positive_factors': prediction.positive_factors,
                        'investment_advice': prediction.investment_advice,
                        'scores': {
                            'mathematical_score': prediction.mathematical_score,
                            'gmp_score': prediction.gmp_score,
                            'subscription_score': prediction.subscription_score,
                            'final_score': prediction.final_score
                        }
                    },
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                ipo_analyses.append(analysis)
            
            # Generate summary
            summary = self._generate_analysis_summary(ipo_analyses, gmp_data)
            
            # Save comprehensive analysis
            complete_analysis = {
                'success': True,
                'analysis_timestamp': datetime.now().isoformat(),
                'total_ipos_analyzed': len(ipo_analyses),
                'gmp_data_status': {
                    'sources_scraped': gmp_data.get('sources_scraped', []),
                    'total_gmp_ipos': gmp_data.get('total_ipos', 0),
                    'scraping_errors': gmp_data.get('errors', [])
                },
                'summary': summary,
                'ipo_analyses': ipo_analyses
            }
            
            # Save to file
            self.file_storage.save_data('ipo_gmp_analysis', complete_analysis)
            
            return complete_analysis
            
        except Exception as e:
            logger.error(f"Error in GMP integration analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat(),
                'message': 'Failed to complete GMP integration analysis'
            }
    

    
    def get_ipo_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Get specific IPO recommendation"""
        
        try:
            # Load latest analysis
            analysis_data = self.file_storage.load_data('ipo_gmp_analysis')
            
            if not analysis_data:
                return {
                    'success': False,
                    'message': 'No analysis data available. Run analysis first.'
                }
            
            # Find specific IPO
            for analysis in analysis_data.get('data', {}).get('ipo_analyses', []):
                ipo_symbol = analysis.get('ipo_details', {}).get('symbol', '')
                if ipo_symbol.upper() == symbol.upper():
                    return {
                        'success': True,
                        'symbol': symbol,
                        'recommendation': analysis.get('prediction', {}),
                        'ipo_details': analysis.get('ipo_details', {}),
                        'gmp_data': analysis.get('gmp_data', {}),
                        'subscription_data': analysis.get('subscription_data', {}),
                        'analysis_timestamp': analysis.get('analysis_timestamp')
                    }
            
            return {
                'success': False,
                'message': f'IPO {symbol} not found in analysis data'
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendation for {symbol}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_top_recommendations(self, limit: int = 5) -> Dict[str, Any]:
        """Get top IPO recommendations based on analysis"""
        
        try:
            # Load latest analysis
            analysis_data = self.file_storage.load_data('ipo_gmp_analysis')
            
            if not analysis_data:
                return {
                    'success': False,
                    'message': 'No analysis data available. Run analysis first.'
                }
            
            # Sort by final score
            ipo_analyses = analysis_data.get('data', {}).get('ipo_analyses', [])
            
            sorted_ipos = sorted(
                ipo_analyses,
                key=lambda x: x.get('prediction', {}).get('scores', {}).get('final_score', 0),
                reverse=True
            )
            
            top_recommendations = []
            
            for analysis in sorted_ipos[:limit]:
                prediction = analysis.get('prediction', {})
                ipo_details = analysis.get('ipo_details', {})
                
                recommendation = {
                    'symbol': ipo_details.get('symbol', ''),
                    'company_name': ipo_details.get('company_name', ''),
                    'recommendation': prediction.get('recommendation', ''),
                    'risk_level': prediction.get('risk_level', ''),
                    'confidence_score': prediction.get('confidence_score', 0),
                    'expected_listing_gain': prediction.get('expected_listing_gain', 0),
                    'final_score': prediction.get('scores', {}).get('final_score', 0),
                    'key_highlights': prediction.get('positive_factors', [])[:3]
                }
                
                top_recommendations.append(recommendation)
            
            return {
                'success': True,
                'total_analyzed': len(ipo_analyses),
                'top_recommendations': top_recommendations,
                'analysis_timestamp': analysis_data.get('data', {}).get('analysis_timestamp')
            }
            
        except Exception as e:
            logger.error(f"Error getting top recommendations: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_gmp_data(self) -> Dict[str, Any]:
        """Update GMP data independently"""
        
        try:
            logger.info("Updating GMP data...")
            
            # Scrape latest GMP data
            gmp_data = self.gmp_scraper.scrape_gmp_data()
            
            # Save GMP data separately
            if gmp_data.get('success'):
                saved = self.file_storage.save_data('latest_gmp_data', gmp_data)
                
                return {
                    'success': True,
                    'message': f'GMP data updated successfully',
                    'sources_scraped': gmp_data.get('sources_scraped', []),
                    'total_ipos': gmp_data.get('total_ipos', 0),
                    'saved_to_file': saved,
                    'timestamp': gmp_data.get('timestamp'),
                    'errors': gmp_data.get('errors', [])
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to scrape GMP data',
                    'errors': gmp_data.get('errors', [])
                }
                
        except Exception as e:
            logger.error(f"Error updating GMP data: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to update GMP data'
            }
    
    def _load_subscription_data(self) -> Dict[str, Any]:
        """Load subscription data from active category files"""
        
        try:
            # Load active category data (which contains subscription info)
            subscription_data = {}
            
            active_category_data = self.file_storage.load_data('active_category')
            
            if active_category_data and 'data' in active_category_data:
                for symbol, category_data in active_category_data['data'].items():
                    if isinstance(category_data, dict):
                        subscription_data[symbol] = {
                            'total_subscription': category_data.get('total_subscription', 0),
                            'categories': category_data.get('categories', {}),
                            'status': category_data.get('status', 'Unknown')
                        }
            
            logger.info(f"Loaded subscription data for {len(subscription_data)} symbols")
            return subscription_data
            
        except Exception as e:
            logger.error(f"Error loading subscription data: {e}")
            return {}
    
    def _find_matching_gmp(self, symbol: str, company_name: str, 
                          gmp_data: Dict[str, Any]) -> Optional[Dict]:
        """Find matching GMP data for an IPO"""
        
        # Direct symbol match
        if symbol in gmp_data:
            return gmp_data[symbol]
        
        # Fuzzy matching by company name
        for gmp_symbol, gmp_info in gmp_data.items():
            gmp_company = gmp_info.get('company_name', '').upper()
            
            # Check if company names have significant overlap
            company_words = set(company_name.upper().split())
            gmp_company_words = set(gmp_company.split())
            
            # Remove common words
            common_words = {'LIMITED', 'LTD', 'PRIVATE', 'PVT', 'COMPANY', 'CORP', 'INC'}
            company_words -= common_words
            gmp_company_words -= common_words
            
            # Check overlap
            if company_words and gmp_company_words:
                overlap = len(company_words & gmp_company_words)
                total_words = len(company_words | gmp_company_words)
                
                if overlap / total_words > 0.5:  # 50% overlap
                    return gmp_info
        
        return None
    
    def _generate_analysis_summary(self, ipo_analyses: List[Dict], 
                                 gmp_data: Dict) -> Dict[str, Any]:
        """Generate analysis summary"""
        
        try:
            summary = {
                'total_ipos': len(ipo_analyses),
                'ai_recommendations': {'BUY': 0, 'HOLD': 0, 'AVOID': 0},
                'gmp_recommendations': {'BUY': 0, 'HOLD': 0, 'AVOID': 0, 'NEUTRAL': 0},
                'risk_levels': {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0},
                'average_expected_gain_ai': 0,
                'average_expected_gain_gmp': 0,
                'best_opportunity': None,
                'highest_risk': None,
                'gmp_coverage': 0,
                'high_agreement_count': 0
            }
            
            if not ipo_analyses:
                return summary
            
            # Count recommendations and collect metrics
            ai_gains = []
            gmp_gains = []
            combined_scores = []
            
            for analysis in ipo_analyses:
                prediction = analysis.get('prediction', {})
                gmp_metrics = analysis.get('gmp_metrics', {})
                combined_analysis = analysis.get('combined_analysis', {})
                
                # Count AI recommendations
                ai_rec = prediction.get('recommendation', 'AVOID')
                summary['ai_recommendations'][ai_rec] = summary['ai_recommendations'].get(ai_rec, 0) + 1
                
                # Count GMP recommendations
                gmp_rec = gmp_metrics.get('gmp_recommendation', 'NEUTRAL')
                summary['gmp_recommendations'][gmp_rec] = summary['gmp_recommendations'].get(gmp_rec, 0) + 1
                
                # Count risk levels
                risk = prediction.get('risk_level', 'HIGH')
                summary['risk_levels'][risk] = summary['risk_levels'].get(risk, 0) + 1
                
                # Track gains
                ai_gain = prediction.get('expected_listing_gain', 0)
                gmp_gain = gmp_metrics.get('consensus_gain', 0)
                ai_gains.append(ai_gain)
                if gmp_metrics.get('has_gmp_data'):
                    gmp_gains.append(gmp_gain)
                
                # Track agreement
                agreement_score = combined_analysis.get('agreement_score', 0)
                if agreement_score >= 70:
                    summary['high_agreement_count'] += 1
                
                # Track best and worst
                combined_score = analysis.get('combined_score', 0)
                combined_scores.append(combined_score)
                
                # Count GMP coverage
                if gmp_metrics.get('has_gmp_data'):
                    summary['gmp_coverage'] += 1
            
            # Calculate averages
            if ai_gains:
                summary['average_expected_gain_ai'] = round(sum(ai_gains) / len(ai_gains), 2)
            if gmp_gains:
                summary['average_expected_gain_gmp'] = round(sum(gmp_gains) / len(gmp_gains), 2)
            
            # Find best and worst based on combined scores
            if combined_scores:
                max_idx = combined_scores.index(max(combined_scores))
                min_idx = combined_scores.index(min(combined_scores))
                
                best_analysis = ipo_analyses[max_idx]
                worst_analysis = ipo_analyses[min_idx]
                
                summary['best_opportunity'] = {
                    'symbol': best_analysis.get('ipo_details', {}).get('symbol', ''),
                    'company_name': best_analysis.get('ipo_details', {}).get('company_name', ''),
                    'combined_score': combined_scores[max_idx],
                    'final_recommendation': best_analysis.get('combined_analysis', {}).get('final_recommendation', '')
                }
                
                summary['highest_risk'] = {
                    'symbol': worst_analysis.get('ipo_details', {}).get('symbol', ''),
                    'company_name': worst_analysis.get('ipo_details', {}).get('company_name', ''),
                    'combined_score': combined_scores[min_idx],
                    'final_recommendation': worst_analysis.get('combined_analysis', {}).get('final_recommendation', '')
                }
            
            summary['gmp_coverage_percent'] = round((summary['gmp_coverage'] / summary['total_ipos']) * 100, 1) if summary['total_ipos'] > 0 else 0
            summary['agreement_rate'] = round((summary['high_agreement_count'] / summary['total_ipos']) * 100, 1) if summary['total_ipos'] > 0 else 0
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
            return {'error': str(e)}

# Create service instance
gmp_integration_service = GMPIntegrationService()