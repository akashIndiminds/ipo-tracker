# app/services/scheduler_service.py
"""
Background Scheduler Service
Runs 4 times daily to scrape and update all data
No API dependency - runs independently
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

class DataSchedulerService:
    """Background scheduler for automated data updates"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_run = None
        self.next_run = None
        
        # Schedule times (IST)
        self.schedule_times = [
            "09:00",  # Market opens
            "12:00",  # Mid-day
            "15:30",  # Market closes
            "18:00"   # Evening update
        ]
    
    async def initialize(self):
        """Initialize scheduler with cron jobs"""
        logger.info("🕐 Initializing Background Scheduler...")
        
        # Schedule data refresh 4 times daily
        for schedule_time in self.schedule_times:
            hour, minute = schedule_time.split(":")
            
            self.scheduler.add_job(
                self.run_complete_data_refresh,
                CronTrigger(hour=int(hour), minute=int(minute)),
                id=f"data_refresh_{schedule_time.replace(':', '')}",
                name=f"Data Refresh at {schedule_time}",
                max_instances=1,  # Prevent overlapping runs
                coalesce=True     # If missed, run once
            )
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"✅ Scheduler started - Updates at: {', '.join(self.schedule_times)}")
        
        # Run immediately on startup if no data exists
        await self._check_and_run_initial_refresh()
    
    async def _check_and_run_initial_refresh(self):
        """Run initial refresh if no data exists"""
        try:
            from ..utils.file_storage import file_storage
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Check if today's data exists
            current_data = file_storage.load_data("nse/current", current_date)
            
            if not current_data:
                logger.info("🚀 No data found - Running initial refresh...")
                await self.run_complete_data_refresh()
            else:
                logger.info("✅ Data already exists for today")
                
        except Exception as e:
            logger.error(f"Initial refresh check error: {e}")
    
    async def run_complete_data_refresh(self):
        """
        Complete data refresh pipeline
        This is the ONLY place where scraping happens
        """
        start_time = datetime.now()
        logger.info("=" * 80)
        logger.info(f"🔄 STARTING COMPLETE DATA REFRESH - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        results = {
            'timestamp': start_time.isoformat(),
            'date': current_date,
            'steps': []
        }
        
        try:
            # Step 1: Fetch NSE Current IPOs
            logger.info("📊 Step 1/7: Fetching Current IPOs from NSE...")
            result = await self._fetch_nse_current()
            results['steps'].append({'name': 'nse_current', 'success': result['success']})
            
            if not result['success']:
                logger.error("❌ Current IPOs fetch failed - stopping pipeline")
                return results
            
            # Step 2: Fetch NSE Upcoming IPOs
            logger.info("📅 Step 2/7: Fetching Upcoming IPOs from NSE...")
            result = await self._fetch_nse_upcoming()
            results['steps'].append({'name': 'nse_upcoming', 'success': result['success']})
            
            # Step 3: Fetch Subscription Data
            logger.info("📈 Step 3/7: Fetching Subscription Data from NSE...")
            result = await self._fetch_subscription_data()
            results['steps'].append({'name': 'subscription', 'success': result['success']})
            
            # Step 4: Fetch GMP Data
            logger.info("💰 Step 4/7: Scraping GMP Data from web...")
            result = await self._fetch_gmp_data()
            results['steps'].append({'name': 'gmp', 'success': result['success']})
            
            # Step 5: Generate Math Predictions
            logger.info("🔢 Step 5/7: Generating Math Predictions...")
            result = await self._generate_math_predictions(current_date)
            results['steps'].append({'name': 'math_predictions', 'success': result['success']})
            
            # Step 6: Generate AI Predictions
            logger.info("🤖 Step 6/7: Generating AI Predictions...")
            result = await self._generate_ai_predictions(current_date)
            results['steps'].append({'name': 'ai_predictions', 'success': result['success']})
            
            # Step 7: Generate Final Predictions
            logger.info("🎯 Step 7/7: Generating Final Combined Predictions...")
            result = await self._generate_final_predictions(current_date)
            results['steps'].append({'name': 'final_predictions', 'success': result['success']})
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            success_count = sum(1 for step in results['steps'] if step['success'])
            total_count = len(results['steps'])
            
            logger.info("=" * 80)
            logger.info(f"✅ DATA REFRESH COMPLETE - {duration:.1f}s")
            logger.info(f"📊 Success: {success_count}/{total_count} steps")
            logger.info("=" * 80)
            
            self.last_run = end_time
            results['duration_seconds'] = duration
            results['success_rate'] = f"{(success_count/total_count)*100:.1f}%"
            
            # Save refresh log
            self._save_refresh_log(results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Data refresh failed: {e}", exc_info=True)
            results['error'] = str(e)
            return results
    
    async def _fetch_nse_current(self) -> Dict:
        """Fetch current IPOs from NSE"""
        try:
            from ..controllers.nse_controller import nse_controller
            result = await nse_controller.get_current_ipos(save_data=True)
            return {'success': result.get('success', False)}
        except Exception as e:
            logger.error(f"NSE Current fetch error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _fetch_nse_upcoming(self) -> Dict:
        """Fetch upcoming IPOs from NSE"""
        try:
            from ..controllers.nse_controller import nse_controller
            result = await nse_controller.get_upcoming_ipos(save_data=True)
            return {'success': result.get('success', False)}
        except Exception as e:
            logger.error(f"NSE Upcoming fetch error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _fetch_subscription_data(self) -> Dict:
        """Fetch subscription data from NSE"""
        try:
            from ..controllers.nse_controller import nse_controller
            result = await nse_controller.get_all_subscriptions(save_data=True)
            return {'success': result.get('success', False)}
        except Exception as e:
            logger.error(f"Subscription fetch error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _fetch_gmp_data(self) -> Dict:
        """Fetch GMP data from web"""
        try:
            from ..controllers.gmp_controller import gmp_controller
            result = await gmp_controller.fetch_gmp_data()
            return {'success': result.get('success', False)}
        except Exception as e:
            logger.error(f"GMP fetch error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _generate_math_predictions(self, date: str) -> Dict:
        """Generate math predictions"""
        try:
            from ..controllers.math_controller import math_controller
            result = await math_controller.predict_all_by_date(date)
            return {'success': result.get('success', False)}
        except Exception as e:
            logger.error(f"Math predictions error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _generate_ai_predictions(self, date: str) -> Dict:
        """Generate AI predictions"""
        try:
            from ..controllers.ai_controller import ai_controller
            result = await ai_controller.predict_all_current_ipos(date)
            return {'success': result.get('success', False)}
        except Exception as e:
            logger.error(f"AI predictions error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _generate_final_predictions(self, date: str) -> Dict:
        """Generate final combined predictions"""
        try:
            from ..controllers.final_controller import final_controller
            result = await final_controller.process_all_ipos(date)
            return {'success': result.get('success', False)}
        except Exception as e:
            logger.error(f"Final predictions error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_refresh_log(self, results: Dict):
        """Save refresh log for monitoring"""
        try:
            from ..utils.file_storage import file_storage
            log_date = datetime.now().strftime('%Y-%m-%d')
            file_storage.save_data("logs/refresh", results, log_date)
        except Exception as e:
            logger.error(f"Log save error: {e}")
    
    async def manual_refresh(self) -> Dict:
        """Manually trigger data refresh (for admin use)"""
        logger.info("🔄 Manual refresh triggered")
        return await self.run_complete_data_refresh()
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        next_run = self.scheduler.get_jobs()[0].next_run_time if self.scheduler.get_jobs() else None
        
        return {
            'is_running': self.is_running,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': next_run.isoformat() if next_run else None,
            'schedule_times': self.schedule_times,
            'active_jobs': len(self.scheduler.get_jobs())
        }
    
    async def shutdown(self):
        """Gracefully shutdown scheduler"""
        logger.info("🛑 Shutting down scheduler...")
        self.scheduler.shutdown()
        self.is_running = False

# Create singleton instance
data_scheduler = DataSchedulerService()