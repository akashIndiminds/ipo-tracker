# app/services/data_orchestrator.py
"""
Data Orchestrator Service
Handles sequential data fetching and ensures all dependencies are met
"""

import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DataOrchestrator:
    """Orchestrates all data fetching in correct order"""
    
    def __init__(self):
        self.status = {
            'current_ipos': {'loaded': False, 'error': None, 'timestamp': None},
            'upcoming_ipos': {'loaded': False, 'error': None, 'timestamp': None},
            'subscription': {'loaded': False, 'error': None, 'timestamp': None},
            'gmp': {'loaded': False, 'error': None, 'timestamp': None},
            'math': {'loaded': False, 'error': None, 'timestamp': None},
            'ai': {'loaded': False, 'error': None, 'timestamp': None},
            'final': {'loaded': False, 'error': None, 'timestamp': None}
        }
    
    async def initialize_all_data(self, date: Optional[str] = None) -> Dict:
        """
        Complete data initialization sequence
        Runs all steps in correct order with dependency checking
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"🚀 Starting complete data initialization for {date}")
        
        results = {
            'date': date,
            'started_at': datetime.now().isoformat(),
            'steps': [],
            'success': False,
            'errors': []
        }
        
        try:
            # Step 1: Fetch Current IPOs (CRITICAL - everything depends on this)
            logger.info("📊 Step 1/7: Fetching Current IPOs...")
            current_result = await self._fetch_current_ipos()
            results['steps'].append({
                'name': 'current_ipos',
                'success': current_result['success'],
                'message': current_result.get('message'),
                'count': current_result.get('count', 0)
            })
            
            if not current_result['success']:
                results['errors'].append('Failed to fetch current IPOs - cannot proceed')
                return self._finalize_results(results)
            
            # Step 2: Fetch Upcoming IPOs (independent, can run parallel)
            logger.info("📅 Step 2/7: Fetching Upcoming IPOs...")
            upcoming_result = await self._fetch_upcoming_ipos()
            results['steps'].append({
                'name': 'upcoming_ipos',
                'success': upcoming_result['success'],
                'message': upcoming_result.get('message'),
                'count': upcoming_result.get('count', 0)
            })
            
            # Step 3: Fetch Subscription Data (depends on current IPOs)
            logger.info("📈 Step 3/7: Fetching Subscription Data...")
            subscription_result = await self._fetch_subscription_data()
            results['steps'].append({
                'name': 'subscription',
                'success': subscription_result['success'],
                'message': subscription_result.get('message'),
                'count': subscription_result.get('count', 0)
            })
            
            if not subscription_result['success']:
                results['errors'].append('Subscription data failed - predictions may be limited')
            
            # Step 4: Fetch GMP Data (depends on current IPOs)
            logger.info("💰 Step 4/7: Fetching GMP Data...")
            gmp_result = await self._fetch_gmp_data()
            results['steps'].append({
                'name': 'gmp',
                'success': gmp_result['success'],
                'message': gmp_result.get('message'),
                'matched': gmp_result.get('matched_gmp_entries', 0)
            })
            
            # Step 5: Generate Math Predictions (depends on current + subscription)
            logger.info("🔢 Step 5/7: Generating Math Predictions...")
            math_result = await self._generate_math_predictions(date)
            results['steps'].append({
                'name': 'math_predictions',
                'success': math_result['success'],
                'message': math_result.get('message'),
                'count': math_result.get('summary', {}).get('successful_predictions', 0)
            })
            
            # Step 6: Generate AI Predictions (depends on current IPOs)
            logger.info("🤖 Step 6/7: Generating AI Predictions...")
            ai_result = await self._generate_ai_predictions(date)
            results['steps'].append({
                'name': 'ai_predictions',
                'success': ai_result['success'],
                'message': ai_result.get('message'),
                'count': ai_result.get('total_predictions', 0)
            })
            
            # Step 7: Generate Final Predictions (depends on all above)
            logger.info("🎯 Step 7/7: Generating Final Predictions...")
            final_result = await self._generate_final_predictions(date)
            results['steps'].append({
                'name': 'final_predictions',
                'success': final_result['success'],
                'message': final_result.get('message'),
                'count': final_result.get('summary', {}).get('total', 0)
            })
            
            # Overall success if critical steps succeeded
            critical_steps = ['current_ipos', 'final_predictions']
            results['success'] = all(
                step['success'] for step in results['steps'] 
                if step['name'] in critical_steps
            )
            
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}", exc_info=True)
            results['errors'].append(str(e))
            results['success'] = False
        
        return self._finalize_results(results)
    
    async def _fetch_current_ipos(self) -> Dict:
        """Step 1: Fetch current IPOs from NSE"""
        try:
            from ..controllers.nse_controller import nse_controller
            result = await nse_controller.get_current_ipos(save_data=True)
            
            self.status['current_ipos']['loaded'] = result.get('success', False)
            self.status['current_ipos']['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"Current IPOs fetch failed: {e}")
            self.status['current_ipos']['error'] = str(e)
            return {'success': False, 'message': str(e)}
    
    async def _fetch_upcoming_ipos(self) -> Dict:
        """Step 2: Fetch upcoming IPOs from NSE"""
        try:
            from ..controllers.nse_controller import nse_controller
            result = await nse_controller.get_upcoming_ipos(save_data=True)
            
            self.status['upcoming_ipos']['loaded'] = result.get('success', False)
            self.status['upcoming_ipos']['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"Upcoming IPOs fetch failed: {e}")
            self.status['upcoming_ipos']['error'] = str(e)
            return {'success': False, 'message': str(e)}
    
    async def _fetch_subscription_data(self) -> Dict:
        """Step 3: Fetch subscription data for all current IPOs"""
        try:
            from ..controllers.nse_controller import nse_controller
            result = await nse_controller.get_all_subscriptions(save_data=True)
            
            self.status['subscription']['loaded'] = result.get('success', False)
            self.status['subscription']['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"Subscription data fetch failed: {e}")
            self.status['subscription']['error'] = str(e)
            return {'success': False, 'message': str(e)}
    
    async def _fetch_gmp_data(self) -> Dict:
        """Step 4: Fetch and filter GMP data"""
        try:
            from ..controllers.gmp_controller import gmp_controller
            result = await gmp_controller.fetch_gmp_data()
            
            self.status['gmp']['loaded'] = result.get('success', False)
            self.status['gmp']['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"GMP data fetch failed: {e}")
            self.status['gmp']['error'] = str(e)
            return {'success': False, 'message': str(e)}
    
    async def _generate_math_predictions(self, date: str) -> Dict:
        """Step 5: Generate math predictions"""
        try:
            from ..controllers.math_controller import math_controller
            result = await math_controller.predict_all_by_date(date)
            
            self.status['math']['loaded'] = result.get('success', False)
            self.status['math']['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"Math predictions failed: {e}")
            self.status['math']['error'] = str(e)
            return {'success': False, 'message': str(e)}
    
    async def _generate_ai_predictions(self, date: str) -> Dict:
        """Step 6: Generate AI predictions"""
        try:
            from ..controllers.ai_controller import ai_controller
            result = await ai_controller.predict_all_current_ipos(date)
            
            self.status['ai']['loaded'] = result.get('success', False)
            self.status['ai']['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"AI predictions failed: {e}")
            self.status['ai']['error'] = str(e)
            return {'success': False, 'message': str(e)}
    
    async def _generate_final_predictions(self, date: str) -> Dict:
        """Step 7: Generate final combined predictions"""
        try:
            from ..controllers.final_controller import final_controller
            result = await final_controller.process_all_ipos(date)
            
            self.status['final']['loaded'] = result.get('success', False)
            self.status['final']['timestamp'] = datetime.now().isoformat()
            
            return result
        except Exception as e:
            logger.error(f"Final predictions failed: {e}")
            self.status['final']['error'] = str(e)
            return {'success': False, 'message': str(e)}
    
    def _finalize_results(self, results: Dict) -> Dict:
        """Add final metadata to results"""
        results['completed_at'] = datetime.now().isoformat()
        results['status'] = self.status
        
        # Calculate success rate
        total_steps = len(results['steps'])
        successful_steps = sum(1 for step in results['steps'] if step['success'])
        results['success_rate'] = round((successful_steps / total_steps) * 100, 1) if total_steps > 0 else 0
        
        logger.info(f"✅ Orchestration complete: {successful_steps}/{total_steps} steps successful")
        
        return results
    
    def get_status(self) -> Dict:
        """Get current status of all data"""
        return {
            'status': self.status,
            'timestamp': datetime.now().isoformat()
        }
    
    async def refresh_specific_data(self, data_type: str, date: Optional[str] = None) -> Dict:
        """Refresh specific data type only"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        refresh_methods = {
            'current_ipos': self._fetch_current_ipos,
            'upcoming_ipos': self._fetch_upcoming_ipos,
            'subscription': self._fetch_subscription_data,
            'gmp': self._fetch_gmp_data,
            'math': lambda: self._generate_math_predictions(date),
            'ai': lambda: self._generate_ai_predictions(date),
            'final': lambda: self._generate_final_predictions(date)
        }
        
        if data_type not in refresh_methods:
            return {
                'success': False,
                'message': f'Invalid data type: {data_type}',
                'valid_types': list(refresh_methods.keys())
            }
        
        logger.info(f"🔄 Refreshing {data_type}...")
        return await refresh_methods[data_type]()

# Create singleton instance
data_orchestrator = DataOrchestrator()