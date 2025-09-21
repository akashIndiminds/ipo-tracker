from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Data processing and transformation utilities"""
    
    @staticmethod
    def clean_ipo_data(raw_data: List[Dict]) -> List[Dict]:
        """Clean and standardize IPO data"""
        if not raw_data:
            return []
        
        cleaned_data = []
        
        for item in raw_data:
            try:
                cleaned_item = {
                    'symbol': item.get('symbol', '').strip(),
                    'company_name': item.get('companyName', '').strip(),
                    'series': item.get('series', '').strip(),
                    'issue_start_date': item.get('issueStartDate', ''),
                    'issue_end_date': item.get('issueEndDate', ''),
                    'issue_price': item.get('issuePrice', ''),
                    'issue_size': item.get('issueSize', ''),
                    'status': item.get('status', ''),
                    'subscription_times': item.get('noOfTime', ''),
                    'shares_offered': item.get('noOfSharesOffered', ''),
                    'shares_bid': item.get('noOfsharesBid', '')
                }
                
                # Only add if essential fields are present
                if cleaned_item['symbol'] and cleaned_item['company_name']:
                    cleaned_data.append(cleaned_item)
                    
            except Exception as e:
                logger.warning(f"Error processing IPO item: {e}")
                continue
        
        logger.info(f"Processed {len(cleaned_data)} IPO records from {len(raw_data)} raw records")
        return cleaned_data
    
    @staticmethod
    def clean_market_data(raw_data: List[Dict]) -> List[Dict]:
        """Clean and standardize market indices data"""
        if not raw_data:
            return []
        
        cleaned_data = []
        
        for item in raw_data:
            try:
                cleaned_item = {
                    'index_name': item.get('indexName', '').strip(),
                    'last': DataProcessor._safe_float(item.get('last')),
                    'open': DataProcessor._safe_float(item.get('open')),
                    'high': DataProcessor._safe_float(item.get('high')),
                    'low': DataProcessor._safe_float(item.get('low')),
                    'previous_close': DataProcessor._safe_float(item.get('previousClose')),
                    'change': DataProcessor._safe_float(item.get('change')),
                    'percent_change': DataProcessor._safe_float(item.get('percChange')),
                    'year_high': DataProcessor._safe_float(item.get('yearHigh')),
                    'year_low': DataProcessor._safe_float(item.get('yearLow')),
                    'time_val': item.get('timeVal', '')
                }
                
                # Only add if essential fields are present
                if cleaned_item['index_name']:
                    cleaned_data.append(cleaned_item)
                    
            except Exception as e:
                logger.warning(f"Error processing market item: {e}")
                continue
        
        logger.info(f"Processed {len(cleaned_data)} market records from {len(raw_data)} raw records")
        return cleaned_data
    
    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def filter_major_indices(indices_data: List[Dict]) -> List[Dict]:
        """Filter to show only major market indices"""
        major_indices = [
            'NIFTY 50', 'NIFTY BANK', 'NIFTY IT', 'NIFTY FMCG',
            'NIFTY AUTO', 'NIFTY MIDCAP 100', 'NIFTY SMLCAP 100',
            'NIFTY PHARMA', 'NIFTY REALTY', 'NIFTY METAL'
        ]
        
        filtered_data = [
            item for item in indices_data 
            if item.get('index_name') in major_indices
        ]
        
        logger.info(f"Filtered to {len(filtered_data)} major indices from {len(indices_data)} total")
        return filtered_data
    
    @staticmethod
    def calculate_market_sentiment(indices_data: List[Dict]) -> Dict[str, Any]:
        """Calculate market sentiment from indices data"""
        if not indices_data:
            return {
                'sentiment': 'neutral',
                'sentiment_score': 50.0,
                'positive_count': 0,
                'negative_count': 0,
                'total_count': 0
            }
        
        positive_count = 0
        negative_count = 0
        total_count = len(indices_data)
        
        for index in indices_data:
            percent_change = index.get('percent_change', 0)
            if percent_change and percent_change > 0:
                positive_count += 1
            elif percent_change and percent_change < 0:
                negative_count += 1
        
        sentiment_score = (positive_count / total_count) * 100 if total_count > 0 else 50
        
        if sentiment_score > 60:
            sentiment = 'positive'
        elif sentiment_score < 40:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'sentiment_score': round(sentiment_score, 1),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'total_count': total_count
        }
    
    @staticmethod
    def get_market_highlights(indices_data: List[Dict]) -> Dict[str, Any]:
        """Generate market highlights from indices data"""
        if not indices_data:
            return {"message": "No data available for highlights"}
        
        highlights = {
            "top_gainers": [],
            "top_losers": [],
            "most_active": []
        }
        
        try:
            # Sort by percentage change
            sorted_by_change = sorted(
                [idx for idx in indices_data if idx.get('percent_change') is not None],
                key=lambda x: x.get('percent_change', 0),
                reverse=True
            )
            
            # Top gainers (positive change)
            gainers = [idx for idx in sorted_by_change if idx.get('percent_change', 0) > 0]
            highlights["top_gainers"] = gainers[:3]
            
            # Top losers (negative change)
            losers = [idx for idx in sorted_by_change if idx.get('percent_change', 0) < 0]
            highlights["top_losers"] = losers[-3:]
            
            # Most active (highest volume/movement)
            highlights["most_active"] = sorted_by_change[:5]
            
        except Exception as e:
            logger.warning(f"Error generating market highlights: {e}")
            highlights["error"] = "Could not generate highlights"
        
        return highlights
    
    @staticmethod
    def format_ipo_summary(current_ipos: List[Dict], upcoming_ipos: List[Dict], past_ipos: List[Dict]) -> Dict[str, Any]:
        """Format comprehensive IPO summary"""
        return {
            "current_ipos": {
                "count": len(current_ipos),
                "data": current_ipos[:5],  # Show first 5
                "status": "active" if current_ipos else "none"
            },
            "upcoming_ipos": {
                "count": len(upcoming_ipos),
                "data": upcoming_ipos[:5],  # Show first 5
                "status": "scheduled" if upcoming_ipos else "none"
            },
            "past_ipos": {
                "count": len(past_ipos),
                "data": past_ipos[:5],  # Show first 5
                "status": "completed" if past_ipos else "none"
            },
            "statistics": {
                "total_active": len(current_ipos),
                "total_upcoming": len(upcoming_ipos),
                "total_past": len(past_ipos),
                "grand_total": len(current_ipos) + len(upcoming_ipos) + len(past_ipos)
            },
            "market_activity": "high" if len(current_ipos) + len(upcoming_ipos) > 5 else "moderate" if len(current_ipos) + len(upcoming_ipos) > 0 else "low"
        }