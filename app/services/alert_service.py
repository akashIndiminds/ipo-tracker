# app/services/alert_service.py

import datetime
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

class AlertService:
    def __init__(self):
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your-email@gmail.com',  # Configure these
            'password': 'your-app-password',     # Use app password
            'recipients': ['admin@yourcompany.com']
        }
        
        self.alert_thresholds = {
            'error_rate': 50,  # Alert if error rate > 50%
            'response_time': 10,  # Alert if response time > 10s
            'down_endpoints': 2   # Alert if > 2 endpoints down
        }
    
    def check_and_send_alerts(self, health_summary: Dict):
        """Check system health and send alerts if needed"""
        alerts = []
        
        # Check overall system health
        if health_summary['overall_status'] == 'degraded':
            alerts.append({
                'type': 'system_degraded',
                'message': f"System performance degraded. Success rate: {health_summary['average_success_rate']:.1f}%"
            })
        
        # Check individual endpoints
        down_endpoints = []
        slow_endpoints = []
        
        for endpoint_name, endpoint_data in health_summary['endpoints'].items():
            if endpoint_data['status'] == 'down':
                down_endpoints.append(endpoint_name)
            
            if endpoint_data['response_time'] > self.alert_thresholds['response_time']:
                slow_endpoints.append(f"{endpoint_name} ({endpoint_data['response_time']:.1f}s)")
        
        if len(down_endpoints) >= self.alert_thresholds['down_endpoints']:
            alerts.append({
                'type': 'multiple_endpoints_down',
                'message': f"Multiple endpoints down: {', '.join(down_endpoints)}"
            })
        
        if slow_endpoints:
            alerts.append({
                'type': 'slow_response',
                'message': f"Slow endpoints detected: {', '.join(slow_endpoints)}"
            })
        
        # Send alerts
        for alert in alerts:
            self._send_email_alert(alert)
    
    def _send_email_alert(self, alert: Dict):
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = f"🚨 IPO Tracker Alert: {alert['type']}"
            
            body = f"""
            IPO Tracker System Alert
            
            Alert Type: {alert['type']}
            Message: {alert['message']}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Please check the system immediately.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"Alert sent: {alert['type']}")
            
        except Exception as e:
            print(f"Failed to send alert: {e}")
