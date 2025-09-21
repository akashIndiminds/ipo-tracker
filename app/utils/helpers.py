import re
from datetime import datetime, timedelta
from typing import Optional, Union, Any, List, Dict

def clean_text(text: str) -> str:
    """Clean and normalize text data"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', str(text).strip())

def extract_number(text: str) -> float:
    """Extract number from text (handles ₹, %, etc.)"""
    if not text:
        return 0.0
    
    # Remove currency symbols and spaces
    cleaned = re.sub(r'[₹,%\s]', '', str(text))
    
    # Extract number
    match = re.search(r'[\d.]+', cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return 0.0
    return 0.0

def parse_date(date_str: str) -> int:
    """Calculate days from today to given date"""
    if not date_str:
        return 0
    
    try:
        # Handle different date formats
        if '-' in date_str:
            if len(date_str.split('-')) == 3 and len(date_str.split('-')[2]) == 4:
                date_obj = datetime.strptime(date_str, '%d-%m-%Y')
            else:
                date_obj = datetime.strptime(date_str, '%d-%b-%Y')
        else:
            date_obj = datetime.strptime(date_str, '%d %b %Y')
        
        today = datetime.now()
        diff = (date_obj - today).days
        return max(0, diff)
    except Exception:
        return 0

def format_currency(amount: Union[int, float]) -> str:
    """Format currency in Indian style"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.1f}L"
    else:
        return f"₹{amount:,.0f}"

def calculate_subscription_rate(shares_offered: str, shares_bid: str) -> float:
    """Calculate subscription rate from shares data"""
    try:
        offered = float(shares_offered) if shares_offered else 0
        bid = float(shares_bid) if shares_bid else 0
        
        if offered > 0:
            return round(bid / offered, 2)
        return 0.0
    except (ValueError, ZeroDivisionError):
        return 0.0

def get_risk_level(subscription_times: float, days_remaining: int) -> str:
    """Calculate risk level based on subscription and time"""
    if subscription_times >= 2.0 and days_remaining > 1:
        return "low"
    elif subscription_times >= 1.0 or days_remaining > 2:
        return "medium"
    else:
        return "high"

def validate_date_range(start_date: str, end_date: str) -> bool:
    """Validate if date range is logical"""
    try:
        start = datetime.strptime(start_date, '%d-%b-%Y')
        end = datetime.strptime(end_date, '%d-%b-%Y')
        return start <= end
    except Exception:
        return False

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with proper sign and decimals"""
    if value > 0:
        return f"+{value:.{decimals}f}%"
    else:
        return f"{value:.{decimals}f}%"

def get_market_timing() -> Dict[str, Any]:
    """Get current market timing information"""
    now = datetime.now()
    
    # Market timings (IST)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    is_market_day = now.weekday() < 5  # Monday to Friday
    is_market_hours = market_open <= now <= market_close
    
    return {
        "current_time": now.strftime("%H:%M:%S"),
        "is_market_day": is_market_day,
        "is_market_hours": is_market_hours and is_market_day,
        "market_status": "open" if (is_market_hours and is_market_day) else "closed",
        "next_open": _get_next_market_open(now),
        "time_to_close": _get_time_to_close(now) if (is_market_hours and is_market_day) else None
    }

def _get_next_market_open(current_time: datetime) -> str:
    """Calculate next market opening time"""
    # If it's weekend, next open is Monday
    if current_time.weekday() >= 5:  # Saturday or Sunday
        days_ahead = 7 - current_time.weekday()
        next_monday = current_time + timedelta(days=days_ahead)
        next_open = next_monday.replace(hour=9, minute=15, second=0, microsecond=0)
        return next_open.strftime("%d-%b-%Y %H:%M")
    
    # If it's a weekday but market is closed
    market_open = current_time.replace(hour=9, minute=15, second=0, microsecond=0)
    
    if current_time < market_open:
        # Market opens today
        return market_open.strftime("%d-%b-%Y %H:%M")
    else:
        # Market opens tomorrow (or Monday if it's Friday)
        if current_time.weekday() == 4:  # Friday
            next_open = current_time + timedelta(days=3)  # Monday
        else:
            next_open = current_time + timedelta(days=1)  # Tomorrow
        
        next_open = next_open.replace(hour=9, minute=15, second=0, microsecond=0)
        return next_open.strftime("%d-%b-%Y %H:%M")

def _get_time_to_close(current_time: datetime) -> str:
    """Calculate time remaining until market close"""
    market_close = current_time.replace(hour=15, minute=30, second=0, microsecond=0)
    
    if current_time < market_close:
        time_diff = market_close - current_time
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m"
    
    return "Market Closed"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized.strip('_')

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def parse_price_range(price_str: str) -> Dict[str, Optional[float]]:
    """Parse price range string like 'Rs.100 to Rs.120'"""
    if not price_str:
        return {"min_price": None, "max_price": None}
    
    # Extract numbers from price string
    numbers = re.findall(r'[\d.]+', price_str)
    
    if len(numbers) >= 2:
        try:
            min_price = float(numbers[0])
            max_price = float(numbers[1])
            return {"min_price": min_price, "max_price": max_price}
        except ValueError:
            pass
    elif len(numbers) == 1:
        try:
            price = float(numbers[0])
            return {"min_price": price, "max_price": price}
        except ValueError:
            pass
    
    return {"min_price": None, "max_price": None}

def calculate_ipo_metrics(ipo_data: Dict) -> Dict[str, Any]:
    """Calculate various IPO metrics"""
    metrics = {}
    
    # Subscription metrics
    subscription_times = ipo_data.get('subscription_times', '')
    if subscription_times and subscription_times.replace('.', '').isdigit():
        sub_rate = float(subscription_times)
        metrics['subscription_status'] = "Oversubscribed" if sub_rate > 1.0 else "Undersubscribed"
        metrics['subscription_multiple'] = f"{sub_rate:.2f}x"
    
    # Price metrics
    price_range = parse_price_range(ipo_data.get('issue_price', ''))
    if price_range['min_price'] and price_range['max_price']:
        metrics['price_band'] = f"₹{price_range['min_price']:.0f} - ₹{price_range['max_price']:.0f}"
        metrics['price_premium'] = ((price_range['max_price'] - price_range['min_price']) / price_range['min_price']) * 100
    
    # Issue size metrics
    issue_size = ipo_data.get('issue_size', '')
    if issue_size.isdigit():
        size_value = int(issue_size)
        metrics['issue_size_formatted'] = format_currency(size_value)
    
    # Timing metrics
    start_date = ipo_data.get('issue_start_date', '')
    end_date = ipo_data.get('issue_end_date', '')
    
    if start_date and end_date:
        days_to_start = parse_date(start_date)
        days_to_end = parse_date(end_date)
        
        metrics['days_to_start'] = days_to_start
        metrics['days_to_end'] = days_to_end
        metrics['ipo_duration'] = days_to_end - days_to_start if days_to_end > days_to_start else 0
        
        if days_to_start > 0:
            metrics['status_detail'] = f"Opens in {days_to_start} days"
        elif days_to_end > 0:
            metrics['status_detail'] = f"Closes in {days_to_end} days"
        else:
            metrics['status_detail'] = "Closed"
    
    return metrics

def get_color_code_for_change(percent_change: float) -> str:
    """Get color code based on percentage change"""
    if percent_change > 2:
        return "dark_green"
    elif percent_change > 0:
        return "light_green"
    elif percent_change > -2:
        return "light_red"
    else:
        return "dark_red"

def format_large_number(number: Union[int, float]) -> str:
    """Format large numbers in readable format"""
    if number >= 1e12:
        return f"{number/1e12:.1f}T"
    elif number >= 1e9:
        return f"{number/1e9:.1f}B"
    elif number >= 1e6:
        return f"{number/1e6:.1f}M"
    elif number >= 1e3:
        return f"{number/1e3:.1f}K"
    else:
        return f"{number:.0f}"