from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

class DataProcessor:
    """Enhanced data processing and transformation utilities"""

    @staticmethod
    def clean_market_data(raw_data: List[Dict]) -> List[Dict]:
        """Clean and standardize market indices data"""
        if not raw_data:
            return []
        
        cleaned_data = []
        
        for item in raw_data:
            try:
                cleaned_item = {
                    'index_name': DataProcessor._clean_text(item.get('indexName', '')),
                    'last': DataProcessor._safe_float(item.get('last')),
                    'open': DataProcessor._safe_float(item.get('open')),
                    'high': DataProcessor._safe_float(item.get('high')),
                    'low': DataProcessor._safe_float(item.get('low')),
                    'previous_close': DataProcessor._safe_float(item.get('previousClose')),
                    'change': DataProcessor._safe_float(item.get('change')),
                    'percent_change': DataProcessor._safe_float(item.get('percChange')),
                    'year_high': DataProcessor._safe_float(item.get('yearHigh')),
                    'year_low': DataProcessor._safe_float(item.get('yearLow')),
                    'time_val': DataProcessor._clean_text(item.get('timeVal', ''))
                }
                
                # Add calculated metrics
                cleaned_item.update(DataProcessor._calculate_market_metrics(cleaned_item))
                
                # Only add if essential fields are present
                if cleaned_item['index_name']:
                    cleaned_data.append(cleaned_item)
                    
            except Exception as e:
                logger.warning(f"Error processing market item: {e}")
                continue
        
        logger.info(f"Processed {len(cleaned_data)} market records from {len(raw_data)} raw records")
        return cleaned_data
    
    @staticmethod
    def _clean_text(text: Any) -> str:
        """Clean text by removing null bytes and extra whitespace"""
        if text is None:
            return ""
        
        # Convert to string and remove null bytes
        clean_text = str(text).replace('\x00', '').replace('\r', '').replace('\n', ' ')
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    @staticmethod
    def _clean_number_text(text: Any) -> str:
        """Clean number text and preserve numeric format"""
        if text is None:
            return ""
        
        # Handle scientific notation like "2.2180828E7"
        try:
            if 'E' in str(text).upper():
                return str(int(float(text)))
            return DataProcessor._clean_text(text)
        except:
            return DataProcessor._clean_text(text)
    
    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == '':
            return None
        try:
            # Handle scientific notation
            if 'E' in str(value).upper():
                return float(value)
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _calculate_ipo_metrics(ipo_data: Dict) -> Dict[str, Any]:
        """Calculate additional IPO metrics"""
        metrics = {}
        
        try:
            # Calculate subscription metrics
            subscription_times = ipo_data.get('subscription_times', '')
            if subscription_times and DataProcessor._is_number(subscription_times):
                sub_rate = float(subscription_times)
                metrics['subscription_status'] = "Oversubscribed" if sub_rate > 1.0 else "Undersubscribed"
                metrics['subscription_level'] = DataProcessor._get_subscription_level(sub_rate)
            
            # Parse price range
            price_range = ipo_data.get('issue_price', '')
            price_info = DataProcessor._parse_price_range(price_range)
            metrics.update(price_info)
            
            # Calculate issue size in readable format
            issue_size = ipo_data.get('issue_size', '')
            if issue_size and DataProcessor._is_number(issue_size):
                size_value = float(issue_size)
                metrics['issue_size_formatted'] = DataProcessor._format_currency(size_value)
                metrics['issue_size_category'] = DataProcessor._get_issue_size_category(size_value)
            
            # Calculate timing metrics
            start_date = ipo_data.get('issue_start_date', '')
            end_date = ipo_data.get('issue_end_date', '')
            
            if start_date and end_date:
                timing_info = DataProcessor._calculate_timing_metrics(start_date, end_date)
                metrics.update(timing_info)
            
            # Risk assessment
            metrics['risk_level'] = DataProcessor._assess_ipo_risk(ipo_data, metrics)
            
        except Exception as e:
            logger.warning(f"Error calculating IPO metrics: {e}")
        
        return metrics
    
    @staticmethod
    def _calculate_market_metrics(market_data: Dict) -> Dict[str, Any]:
        """Calculate additional market metrics"""
        metrics = {}
        
        try:
            last = market_data.get('last')
            high = market_data.get('high')
            low = market_data.get('low')
            year_high = market_data.get('year_high')
            year_low = market_data.get('year_low')
            
            if last and high and low:
                # Daily range
                daily_range = high - low
                metrics['daily_range'] = round(daily_range, 2)
                metrics['daily_range_percent'] = round((daily_range / last) * 100, 2)
                
                # Position within day's range
                if daily_range > 0:
                    position = (last - low) / daily_range
                    metrics['day_position'] = round(position * 100, 1)  # Percentage from low
            
            if last and year_high and year_low:
                # Year range metrics
                year_range = year_high - year_low
                metrics['year_range'] = round(year_range, 2)
                
                # Position within year's range
                if year_range > 0:
                    year_position = (last - year_low) / year_range
                    metrics['year_position'] = round(year_position * 100, 1)
                
                # Distance from highs/lows
                metrics['distance_from_high'] = round(((year_high - last) / year_high) * 100, 2)
                metrics['distance_from_low'] = round(((last - year_low) / year_low) * 100, 2)
            
            # Trend analysis
            percent_change = market_data.get('percent_change')
            if percent_change is not None:
                metrics['trend'] = DataProcessor._get_trend_direction(percent_change)
                metrics['volatility_level'] = DataProcessor._get_volatility_level(abs(percent_change))
        
        except Exception as e:
            logger.warning(f"Error calculating market metrics: {e}")
        
        return metrics
    
    @staticmethod
    def _is_number(text: str) -> bool:
        """Check if text represents a number"""
        try:
            float(text)
            return True
        except:
            return False
    
    @staticmethod
    def _get_subscription_level(subscription_rate: float) -> str:
        """Get subscription level description"""
        if subscription_rate >= 10:
            return "Heavily Oversubscribed"
        elif subscription_rate >= 5:
            return "Highly Oversubscribed"
        elif subscription_rate >= 2:
            return "Well Subscribed"
        elif subscription_rate >= 1:
            return "Fully Subscribed"
        elif subscription_rate >= 0.5:
            return "Moderately Subscribed"
        else:
            return "Poorly Subscribed"
    
    @staticmethod
    def _parse_price_range(price_str: str) -> Dict[str, Any]:
        """Parse price range string"""
        result = {}
        
        if not price_str:
            return result
        
        # Extract numbers from price string
        numbers = re.findall(r'[\d.]+', price_str)
        
        if len(numbers) >= 2:
            try:
                min_price = float(numbers[0])
                max_price = float(numbers[1])
                result['min_price'] = min_price
                result['max_price'] = max_price
                result['price_band_width'] = max_price - min_price
                result['price_band_percent'] = round(((max_price - min_price) / min_price) * 100, 2)
            except ValueError:
                pass
        elif len(numbers) == 1:
            try:
                price = float(numbers[0])
                result['min_price'] = price
                result['max_price'] = price
            except ValueError:
                pass
        
        return result
    
    @staticmethod
    def _format_currency(amount: float) -> str:
        """Format currency in Indian style"""
        if amount >= 10000000:  # 1 crore
            return f"₹{amount/10000000:.1f} Cr"
        elif amount >= 100000:  # 1 lakh
            return f"₹{amount/100000:.1f} L"
        elif amount >= 1000:  # 1 thousand
            return f"₹{amount/1000:.1f} K"
        else:
            return f"₹{amount:,.0f}"
    
    @staticmethod
    def _get_issue_size_category(size: float) -> str:
        """Categorize IPO by issue size"""
        if size >= 5000000000:  # 500 Cr
            return "Large Cap"
        elif size >= 1000000000:  # 100 Cr
            return "Mid Cap"
        elif size >= 250000000:  # 25 Cr
            return "Small Cap"
        else:
            return "Micro Cap"
    
    @staticmethod
    def _calculate_timing_metrics(start_date: str, end_date: str) -> Dict[str, Any]:
        """Calculate timing-related metrics"""
        metrics = {}
        
        try:
            today = datetime.now()
            
            # Parse dates - handle different formats
            start_dt = DataProcessor._parse_date(start_date)
            end_dt = DataProcessor._parse_date(end_date)
            
            if start_dt and end_dt:
                # Days calculations
                days_to_start = (start_dt - today).days
                days_to_end = (end_dt - today).days
                ipo_duration = (end_dt - start_dt).days
                
                metrics['days_to_start'] = max(0, days_to_start)
                metrics['days_to_end'] = max(0, days_to_end)
                metrics['ipo_duration'] = max(0, ipo_duration)
                
                # Status determination
                if days_to_start > 0:
                    metrics['timing_status'] = f"Opens in {days_to_start} days"
                elif days_to_end > 0:
                    metrics['timing_status'] = f"Closes in {days_to_end} days"
                else:
                    metrics['timing_status'] = "Closed"
                
                # Urgency level
                if days_to_end == 1:
                    metrics['urgency'] = "Last Day"
                elif days_to_end <= 2:
                    metrics['urgency'] = "High"
                elif days_to_end <= 5:
                    metrics['urgency'] = "Medium"
                else:
                    metrics['urgency'] = "Low"
        
        except Exception as e:
            logger.warning(f"Error calculating timing metrics: {e}")
        
        return metrics
    
    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string in various formats"""
        if not date_str:
            return None
        
        formats = [
            '%d-%b-%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d %b %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def _assess_ipo_risk(ipo_data: Dict, metrics: Dict) -> str:
        """Assess IPO risk level"""
        risk_factors = 0
        
        # Subscription risk
        subscription_times = ipo_data.get('subscription_times', '')
        if subscription_times and DataProcessor._is_number(subscription_times):
            sub_rate = float(subscription_times)
            if sub_rate < 0.5:
                risk_factors += 2
            elif sub_rate < 1.0:
                risk_factors += 1
        
        # Size risk
        issue_size_category = metrics.get('issue_size_category', '')
        if issue_size_category == 'Micro Cap':
            risk_factors += 2
        elif issue_size_category == 'Small Cap':
            risk_factors += 1
        
        # Price band risk
        price_band_percent = metrics.get('price_band_percent', 0)
        if price_band_percent > 20:
            risk_factors += 1
        
        # Timing risk
        urgency = metrics.get('urgency', '')
        if urgency in ['Last Day', 'High']:
            risk_factors += 1
        
        # Risk level determination
        if risk_factors >= 4:
            return "High"
        elif risk_factors >= 2:
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def _get_trend_direction(percent_change: float) -> str:
        """Get trend direction based on percentage change"""
        if percent_change > 2:
            return "Strong Uptrend"
        elif percent_change > 0.5:
            return "Uptrend"
        elif percent_change > -0.5:
            return "Sideways"
        elif percent_change > -2:
            return "Downtrend"
        else:
            return "Strong Downtrend"
    
    @staticmethod
    def _get_volatility_level(abs_change: float) -> str:
        """Get volatility level"""
        if abs_change > 3:
            return "High"
        elif abs_change > 1.5:
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def filter_major_indices(indices_data: List[Dict]) -> List[Dict]:
        """Filter to show only major market indices"""
        major_indices = [
            'NIFTY 50', 'NIFTY BANK', 'NIFTY IT', 'NIFTY FMCG',
            'NIFTY AUTO', 'NIFTY MIDCAP 100', 'NIFTY SMLCAP 100',
            'NIFTY PHARMA', 'NIFTY REALTY', 'NIFTY METAL',
            'NIFTY ENERGY', 'NIFTY INFRA', 'NIFTY PSU BANK'
        ]
        
        filtered_data = [
            item for item in indices_data 
            if item.get('index_name') in major_indices
        ]
        
        logger.info(f"Filtered to {len(filtered_data)} major indices from {len(indices_data)} total")
        return filtered_data
    
    @staticmethod
    def calculate_market_sentiment(indices_data: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive market sentiment"""
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
        total_weighted_change = 0
        total_count = len(indices_data)
        
        # Weight major indices more heavily
        major_indices_weights = {
            'NIFTY 50': 3,
            'NIFTY BANK': 2,
            'NIFTY IT': 2,
            'NIFTY MIDCAP 100': 1.5,
            'NIFTY SMLCAP 100': 1.5
        }
        
        total_weight = 0
        
        for index in indices_data:
            index_name = index.get('index_name', '')
            percent_change = index.get('percent_change', 0)
            weight = major_indices_weights.get(index_name, 1)
            
            if percent_change and percent_change > 0:
                positive_count += 1
            elif percent_change and percent_change < 0:
                negative_count += 1
            
            if percent_change:
                total_weighted_change += percent_change * weight
                total_weight += weight
        
        # Calculate weighted sentiment score
        if total_weight > 0:
            avg_weighted_change = total_weighted_change / total_weight
            # Convert to 0-100 scale
            sentiment_score = 50 + (avg_weighted_change * 10)  # Scale factor
            sentiment_score = max(0, min(100, sentiment_score))  # Clamp to 0-100
        else:
            sentiment_score = 50
        
        # Determine sentiment category
        if sentiment_score > 70:
            sentiment = 'very_positive'
        elif sentiment_score > 60:
            sentiment = 'positive'
        elif sentiment_score > 40:
            sentiment = 'neutral'
        elif sentiment_score > 30:
            sentiment = 'negative'
        else:
            sentiment = 'very_negative'
        
        return {
            'sentiment': sentiment,
            'sentiment_score': round(sentiment_score, 1),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'total_count': total_count,
            'weighted_average_change': round(total_weighted_change / total_weight if total_weight > 0 else 0, 3)
        }
    
    @staticmethod
    def get_market_highlights(indices_data: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive market highlights"""
        if not indices_data:
            return {"message": "No data available for highlights"}
        
        highlights = {
            "top_gainers": [],
            "top_losers": [],
            "most_active": [],
            "sector_performance": {}
        }
        
        try:
            # Filter valid data
            valid_indices = [idx for idx in indices_data if idx.get('percent_change') is not None]
            
            if not valid_indices:
                return highlights
            
            # Sort by percentage change
            sorted_by_change = sorted(valid_indices, key=lambda x: x.get('percent_change', 0), reverse=True)
            
            # Top gainers (positive change)
            gainers = [idx for idx in sorted_by_change if idx.get('percent_change', 0) > 0]
            highlights["top_gainers"] = gainers[:5]
            
            # Top losers (negative change)
            losers = [idx for idx in sorted_by_change if idx.get('percent_change', 0) < 0]
            highlights["top_losers"] = losers[-5:]  # Bottom 5
            
            # Most active (highest absolute change)
            most_active = sorted(valid_indices, key=lambda x: abs(x.get('percent_change', 0)), reverse=True)
            highlights["most_active"] = most_active[:5]
            
            # Sector performance analysis
            sector_mapping = {
                'NIFTY BANK': 'Banking',
                'NIFTY IT': 'Technology',
                'NIFTY PHARMA': 'Pharmaceuticals',
                'NIFTY AUTO': 'Automobile',
                'NIFTY FMCG': 'FMCG',
                'NIFTY METAL': 'Metals',
                'NIFTY REALTY': 'Real Estate',
                'NIFTY ENERGY': 'Energy',
                'NIFTY INFRA': 'Infrastructure'
            }
            
            for index in valid_indices:
                index_name = index.get('index_name', '')
                sector = sector_mapping.get(index_name)
                if sector:
                    highlights["sector_performance"][sector] = {
                        'change': index.get('percent_change', 0),
                        'last': index.get('last'),
                        'trend': DataProcessor._get_trend_direction(index.get('percent_change', 0))
                    }
            
        except Exception as e:
            logger.warning(f"Error generating market highlights: {e}")
            highlights["error"] = "Could not generate highlights"
        
        return highlights
    
    @staticmethod
    def format_ipo_summary(current_ipos: List[Dict], upcoming_ipos: List[Dict], past_ipos: List[Dict], gmp_data: List[Dict] = None) -> Dict[str, Any]:
        """Format comprehensive IPO summary with GMP integration"""
        
        # Merge GMP data with IPO data
        if gmp_data:
            current_ipos = DataProcessor._merge_ipo_gmp_data(current_ipos, gmp_data)
            upcoming_ipos = DataProcessor._merge_ipo_gmp_data(upcoming_ipos, gmp_data)
        
        summary = {
            "current_ipos": {
                "count": len(current_ipos),
                "data": current_ipos[:5],  # Show first 5
                "status": "active" if current_ipos else "none",
                "highlights": DataProcessor._get_ipo_highlights(current_ipos)
            },
            "upcoming_ipos": {
                "count": len(upcoming_ipos),
                "data": upcoming_ipos[:5],  # Show first 5
                "status": "scheduled" if upcoming_ipos else "none",
                "highlights": DataProcessor._get_ipo_highlights(upcoming_ipos)
            },
            "past_ipos": {
                "count": len(past_ipos),
                "data": past_ipos[:5],  # Show first 5
                "status": "completed" if past_ipos else "none",
                "highlights": DataProcessor._get_ipo_highlights(past_ipos)
            },
            "statistics": {
                "total_active": len(current_ipos),
                "total_upcoming": len(upcoming_ipos),
                "total_past": len(past_ipos),
                "grand_total": len(current_ipos) + len(upcoming_ipos) + len(past_ipos)
            },
            "market_activity": DataProcessor._assess_market_activity(current_ipos, upcoming_ipos),
            "investment_insights": DataProcessor._generate_investment_insights(current_ipos, upcoming_ipos, gmp_data)
        }
        
        return summary
    
    @staticmethod
    def _merge_ipo_gmp_data(ipo_data: List[Dict], gmp_data: List[Dict]) -> List[Dict]:
        """Merge IPO data with GMP data"""
        if not gmp_data:
            return ipo_data
        
        # Create a mapping of company names to GMP data
        gmp_mapping = {}
        for gmp_item in gmp_data:
            company_name = gmp_item.get('company_name', '').upper()
            clean_name = re.sub(r'(LIMITED|LTD|PVT|PRIVATE|\.|,)', '', company_name).strip()
            gmp_mapping[clean_name] = gmp_item
        
        # Merge GMP data into IPO data
        merged_data = []
        for ipo in ipo_data:
            ipo_copy = ipo.copy()
            ipo_company = ipo.get('company_name', '').upper()
            clean_ipo_name = re.sub(r'(LIMITED|LTD|PVT|PRIVATE|\.|,)', '', ipo_company).strip()
            
            # Find matching GMP data
            gmp_match = None
            for gmp_key, gmp_value in gmp_mapping.items():
                if gmp_key in clean_ipo_name or clean_ipo_name in gmp_key:
                    gmp_match = gmp_value
                    break
            
            if gmp_match:
                ipo_copy['gmp'] = gmp_match.get('gmp', 0)
                ipo_copy['estimated_listing_gain'] = gmp_match.get('estimated_listing_gain', 0)
                ipo_copy['gmp_sources'] = gmp_match.get('sources', [])
                ipo_copy['gmp_last_updated'] = gmp_match.get('last_updated')
            
            merged_data.append(ipo_copy)
        
        return merged_data
    
    @staticmethod
    def _get_ipo_highlights(ipo_data: List[Dict]) -> Dict[str, Any]:
        """Get highlights for IPO data"""
        if not ipo_data:
            return {}
        
        highlights = {}
        
        try:
            # Most subscribed
            subscribed_ipos = [ipo for ipo in ipo_data if ipo.get('subscription_times') and DataProcessor._is_number(ipo.get('subscription_times', ''))]
            if subscribed_ipos:
                most_subscribed = max(subscribed_ipos, key=lambda x: float(x.get('subscription_times', '0')))
                highlights['most_subscribed'] = {
                    'company': most_subscribed.get('company_name'),
                    'subscription_times': most_subscribed.get('subscription_times')
                }
            
            # Largest by size
            sized_ipos = [ipo for ipo in ipo_data if ipo.get('issue_size') and DataProcessor._is_number(ipo.get('issue_size', ''))]
            if sized_ipos:
                largest_ipo = max(sized_ipos, key=lambda x: float(x.get('issue_size', '0')))
                highlights['largest_issue'] = {
                    'company': largest_ipo.get('company_name'),
                    'size': largest_ipo.get('issue_size_formatted', largest_ipo.get('issue_size'))
                }
            
            # Best GMP (if available)
            gmp_ipos = [ipo for ipo in ipo_data if ipo.get('gmp') is not None]
            if gmp_ipos:
                best_gmp = max(gmp_ipos, key=lambda x: x.get('gmp', 0))
                highlights['best_gmp'] = {
                    'company': best_gmp.get('company_name'),
                    'gmp': best_gmp.get('gmp')
                }
            
            # Closing soon (for current IPOs)
            urgent_ipos = [ipo for ipo in ipo_data if ipo.get('urgency') in ['Last Day', 'High']]
            if urgent_ipos:
                highlights['closing_soon'] = [
                    {
                        'company': ipo.get('company_name'),
                        'urgency': ipo.get('urgency'),
                        'timing_status': ipo.get('timing_status')
                    } for ipo in urgent_ipos[:3]
                ]
        
        except Exception as e:
            logger.warning(f"Error generating IPO highlights: {e}")
        
        return highlights
    
    @staticmethod
    def _assess_market_activity(current_ipos: List[Dict], upcoming_ipos: List[Dict]) -> str:
        """Assess overall IPO market activity"""
        total_active = len(current_ipos) + len(upcoming_ipos)
        
        if total_active >= 10:
            return "Very High"
        elif total_active >= 6:
            return "High"
        elif total_active >= 3:
            return "Moderate"
        elif total_active >= 1:
            return "Low"
        else:
            return "Very Low"
    
    @staticmethod
    def _generate_investment_insights(current_ipos: List[Dict], upcoming_ipos: List[Dict], gmp_data: List[Dict] = None) -> List[str]:
        """Generate investment insights based on current market conditions"""
        insights = []
        
        try:
            total_current = len(current_ipos)
            total_upcoming = len(upcoming_ipos)
            
            # Activity insights
            if total_current + total_upcoming > 8:
                insights.append("📈 High IPO activity in the market - Multiple investment opportunities available")
            elif total_current + total_upcoming < 2:
                insights.append("📊 Low IPO activity - Limited new listing options")
            
            # Subscription insights
            if current_ipos:
                subscribed_count = sum(1 for ipo in current_ipos 
                                     if ipo.get('subscription_times') and 
                                     DataProcessor._is_number(ipo.get('subscription_times', '')) and 
                                     float(ipo.get('subscription_times', '0')) > 1)
                
                if subscribed_count > len(current_ipos) * 0.7:
                    insights.append("🔥 Strong investor demand - Most IPOs are oversubscribed")
                elif subscribed_count < len(current_ipos) * 0.3:
                    insights.append("⚠️ Weak investor sentiment - Many IPOs are undersubscribed")
            
            # GMP insights
            if gmp_data:
                positive_gmp = sum(1 for gmp in gmp_data if gmp.get('gmp', 0) > 0)
                if positive_gmp > len(gmp_data) * 0.6:
                    insights.append("💰 Positive gray market sentiment - Majority IPOs trading at premium")
                elif positive_gmp < len(gmp_data) * 0.4:
                    insights.append("📉 Negative gray market sentiment - Many IPOs trading at discount")
            
            # Size distribution insights
            large_ipos = sum(1 for ipo in current_ipos + upcoming_ipos 
                           if ipo.get('issue_size_category') in ['Large Cap', 'Mid Cap'])
            
            if large_ipos > (total_current + total_upcoming) * 0.5:
                insights.append("🏢 Quality IPO pipeline - Many large and mid-cap companies going public")
            
            # Timing insights
            urgent_ipos = sum(1 for ipo in current_ipos if ipo.get('urgency') in ['Last Day', 'High'])
            if urgent_ipos > 0:
                insights.append(f"⏰ {urgent_ipos} IPO(s) closing soon - Act quickly if interested")
            
            # Default insight if none generated
            if not insights:
                insights.append("📋 Market analysis complete - Review individual IPOs for opportunities")
        
        except Exception as e:
            logger.warning(f"Error generating investment insights: {e}")
            insights.append("📊 Investment insights temporarily unavailable")
        
        return insights
    
    @staticmethod
    def clean_ipo_data(raw_data: List[Dict]) -> List[Dict]:
        """Clean and standardize IPO data with enhanced validation"""
        if not raw_data:
            return []
        
        cleaned_data = []
        
        for item in raw_data:
            try:
                # Clean text fields to remove null bytes and extra whitespace
                cleaned_item = {
                    'symbol': DataProcessor._clean_text(item.get('symbol', '')),
                    'company_name': DataProcessor._clean_text(item.get('companyName', '')),
                    'series': DataProcessor._clean_text(item.get('series', '')),
                    'issue_start_date': DataProcessor._clean_text(item.get('issueStartDate', '')),
                    'issue_end_date': DataProcessor._clean_text(item.get('issueEndDate', '')),
                    'issue_price': DataProcessor._clean_text(item.get('issuePrice', '')),
                    'issue_size': DataProcessor._clean_text(item.get('issueSize', '')),
                    'status': DataProcessor._clean_text(item.get('status', '')),
                    'subscription_times': DataProcessor._format_subscription(DataProcessor._clean_number_text(item.get('noOfTime', ''))),
                    # FIX: Use _safe_int instead of _clean_number_text to ensure int type and default to 0
                    'shares_offered': DataProcessor._safe_int(item.get('noOfSharesOffered', 0)),
                    'shares_bid': DataProcessor._safe_int(item.get('noOfsharesBid', 0))
                }
                
                # Add calculated fields
                cleaned_item.update(DataProcessor._calculate_ipo_metrics(cleaned_item))
                
                # Only add if essential fields are present
                if cleaned_item['symbol'] and cleaned_item['company_name']:
                    cleaned_data.append(cleaned_item)
                    
            except Exception as e:
                logger.warning(f"Error processing IPO item: {e}")
                continue  # FIX: Continue instead of failing the whole list
        
        logger.info(f"Processed {len(cleaned_data)} IPO records from {len(raw_data)} raw records")
        return cleaned_data
    
    @staticmethod
    def _safe_int(value: Any) -> int:
        """Safely convert to int with default 0 (FIX: Added to handle empty strings and parsing)"""
        try:
            if value is None or str(value).strip() == '':
                return 0
            # Handle scientific notation
            if 'E' in str(value).upper():
                return int(float(value))
            clean_value = str(value).replace(",", "").strip()
            return int(float(clean_value))
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def _format_subscription(subscription_times: str) -> str:
        """Format subscription times like '3.07x' (FIX: Ensure always ends with 'x')"""
        try:
            if not subscription_times or subscription_times == "":
                return "0.00x"
            num_value = float(subscription_times)
            return f"{num_value:.2f}x"
        except (ValueError, TypeError):
            return "0.00x"
