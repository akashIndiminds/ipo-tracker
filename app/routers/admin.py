
# app/routers/admin.py

from ast import List
import datetime
import os
from typing import Dict
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from app.services.monitoring_service import MonitoringService
from app.services.enhanced_nse_service import AntiBlockingNSEService
from app.services.backup_service import BackupService

router = APIRouter()
security = HTTPBasic()
monitoring_service = MonitoringService()
backup_service = BackupService()

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Basic authentication for admin endpoints"""
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "your-admin-password")
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@router.get("/health")
async def get_system_health(admin: str = Depends(authenticate_admin)):
    """Get comprehensive system health status"""
    try:
        nse_service = AntiBlockingNSEService()
        health_status = await monitoring_service.check_api_health(nse_service)
        health_summary = monitoring_service.get_system_health_summary()
        
        return {
            "system_health": health_summary,
            "detailed_status": health_status,
            "recommendations": get_health_recommendations(health_summary)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/backup")
async def create_backup(admin: str = Depends(authenticate_admin)):
    """Create manual backup of all data"""
    try:
        nse_service = AntiBlockingNSEService()
        
        # Fetch all data
        current_ipos = nse_service.get_current_ipos()
        upcoming_ipos = nse_service.get_upcoming_ipos()
        past_ipos = nse_service.get_past_ipos(30)
        
        # Create backup
        backup_file = backup_service.backup_ipo_data(current_ipos, upcoming_ipos, past_ipos)
        
        return {
            "message": "Backup created successfully",
            "backup_file": backup_file,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.get("/logs")
async def get_system_logs(limit: int = 100, admin: str = Depends(authenticate_admin)):
    """Get recent system logs"""
    try:
        with open('logs/ipo_tracker.log', 'r') as f:
            lines = f.readlines()
        
        # Return last N lines
        recent_logs = lines[-limit:] if len(lines) > limit else lines
        
        return {
            "logs": recent_logs,
            "total_lines": len(lines),
            "showing": len(recent_logs)
        }
    except Exception as e:
        return {"error": f"Could not read logs: {str(e)}"}

@router.post("/clear-cache")
async def clear_system_cache(admin: str = Depends(authenticate_admin)):
    """Clear all cached data"""
    try:
        cache_dir = "cache"
        if os.path.exists(cache_dir):
            for file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, file))
        
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")

def get_health_recommendations(health_summary: Dict) -> List[str]:
    """Generate recommendations based on health status"""
    recommendations = []
    
    if health_summary['average_success_rate'] < 80:
        recommendations.append("Consider implementing additional fallback data sources")
    
    if health_summary['average_response_time'] > 5:
        recommendations.append("Response times are high - check network connectivity")
    
    if health_summary['overall_status'] == 'degraded':
        recommendations.append("System is degraded - monitor closely and consider maintenance")
    
    failing_endpoints = [
        name for name, data in health_summary['endpoints'].items() 
        if data['status'] == 'down'
    ]
    
    if failing_endpoints:
        recommendations.append(f"Fix failing endpoints: {', '.join(failing_endpoints)}")
    
    if not recommendations:
        recommendations.append("System is running smoothly!")
    
    return recommendations
