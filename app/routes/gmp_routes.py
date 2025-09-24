# app/routes/gmp_routes.py
"""GMP Routes - Grey Market Premium Analysis Endpoints"""

import re
from fastapi import APIRouter, Query, Path
from typing import Dict, Any

from ..controllers.gmp_controller import gmp_controller

# Create router
router = APIRouter(prefix="/api/gmp", tags=["GMP Analysis & Predictions"])

@router.post("/analyze")
async def analyze_current_ipos_with_gmp(
    save_data: bool = Query(True, description="Save analysis to JSON file")
) -> Dict[str, Any]:
    """
    Comprehensive IPO Analysis with GMP Integration
    
    This endpoint combines:
    - NSE current IPO data
    - Grey Market Premium from multiple sources
    - Mathematical prediction modeling
    - Risk assessment and recommendations
    """
    return await gmp_controller.analyze_current_ipos_with_gmp(save_data)

@router.get("/recommendation/{symbol}")
async def get_ipo_recommendation(
    symbol: str = Path(..., description="IPO symbol (e.g., SOLARWORLD)")
) -> Dict[str, Any]:
    """Get specific IPO recommendation with detailed analysis"""
    return await gmp_controller.get_ipo_recommendation(symbol)

@router.get("/top-recommendations")
async def get_top_recommendations(
    limit: int = Query(5, description="Number of top recommendations (1-20)", ge=1, le=20)
) -> Dict[str, Any]:
    """Get top IPO recommendations ranked by prediction score"""
    return await gmp_controller.get_top_recommendations(limit)

@router.post("/update-gmp")
async def update_gmp_data() -> Dict[str, Any]:
    """
    Update GMP Data from External Sources
    
    Scrapes latest Grey Market Premium data from:
    - IPO Watch
    - InvestorGain  
    - Chittorgarh
    - Other reliable sources
    """
    return await gmp_controller.update_gmp_data()

@router.get("/explanation/{symbol}")
async def get_prediction_explanation(
    symbol: str = Path(..., description="IPO symbol")
) -> Dict[str, Any]:
    """
    Get Detailed Prediction Methodology Explanation
    
    Explains:
    - Mathematical scoring components
    - Weight distribution
    - Risk factor analysis
    - Data sources used
    """
    return await gmp_controller.get_prediction_explanation(symbol)

@router.get("/market-summary")
async def get_market_analysis_summary() -> Dict[str, Any]:
    """
    Get Overall IPO Market Analysis Summary
    
    Provides:
    - Market sentiment analysis
    - Risk distribution
    - Expected returns overview
    - Top opportunities
    """
    return await gmp_controller.get_market_analysis_summary()

@router.get("/test-scrape")
async def test_gmp_scraping() -> Dict[str, Any]:
    """
    Test GMP Scraping from IPOWatch
    
    Tests:
    - Direct scraping from ipowatch.in
    - Targets 'wp-block-table is-style-regular' class
    - Stores data in JSON format
    """
    import requests
    from bs4 import BeautifulSoup
    import logging
    from datetime import datetime
    import re
    
    from ..utils.file_storage import file_storage
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Testing IPOWatch GMP scraping...")
        
        # Setup session with headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Scrape IPOWatch
        url = 'https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/'
        
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the specific table class you mentioned
        target_table = soup.find('figure', class_='wp-block-table is-style-regular')
        
        if target_table:
            # Get the actual table inside the figure
            table = target_table.find('table')
        else:
            # Fallback: look for any table
            table = soup.find('table')
            logger.warning("wp-block-table is-style-regular not found, using fallback")
        
        gmp_data = []
        scraped_count = 0
        
        if table:
            rows = table.find_all('tr')
            logger.info(f"Found {len(rows)} rows in table")
            
            # Process each row (skip header)
            for i, row in enumerate(rows[1:], 1):
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 5:  # Need at least 5 columns: Stock, GMP, Price, Gain, Date, Type
                    try:
                        # Extract data from cells
                        stock_cell = cells[0]
                        gmp_cell = cells[1]
                        price_cell = cells[2]  
                        gain_cell = cells[3]
                        date_cell = cells[4]
                        type_cell = cells[5] if len(cells) > 5 else None
                        
                        # Clean text extraction
                        company_name = stock_cell.get_text(strip=True)
                        gmp_text = gmp_cell.get_text(strip=True)
                        price_text = price_cell.get_text(strip=True)
                        gain_text = gain_cell.get_text(strip=True)
                        date_text = date_cell.get_text(strip=True)
                        type_text = type_cell.get_text(strip=True) if type_cell else 'Unknown'
                        
                        # Extract symbol from company name
                        symbol = _extract_symbol_from_name(company_name)
                        
                        # Extract numeric values
                        gmp_value = _extract_number_from_text(gmp_text)
                        issue_price = _extract_number_from_text(price_text)
                        listing_gain = _extract_number_from_text(gain_text)
                        
                        # Create IPO entry
                        if company_name and company_name != 'Stock / IPO':  # Skip header
                            ipo_entry = {
                                'row_number': i,
                                'company_name': company_name,
                                'symbol': symbol,
                                'gmp_text': gmp_text,
                                'gmp_value': gmp_value,
                                'issue_price_text': price_text,
                                'issue_price': issue_price,
                                'estimated_listing_price': (issue_price + gmp_value) if issue_price and gmp_value else None,
                                'gain_text': gain_text,
                                'listing_gain_percent': listing_gain,
                                'date': date_text,
                                'type': type_text,
                                'scraped_at': datetime.now().isoformat(),
                                'source': 'ipowatch'
                            }
                            
                            gmp_data.append(ipo_entry)
                            scraped_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Error parsing row {i}: {e}")
                        continue
        
        # Save to JSON file
        save_data = {
            'success': True,
            'scraped_at': datetime.now().isoformat(),
            'source': 'ipowatch.in',
            'target_url': url,
            'table_class_found': 'wp-block-table is-style-regular' if target_table else 'fallback_table',
            'total_rows_processed': len(rows) - 1 if 'rows' in locals() else 0,
            'successful_extractions': scraped_count,
            'total_ipos': len(gmp_data),
            'data': gmp_data
        }
        
        # Save to file storage
        saved = file_storage.save_data('test_gmp_scraping', save_data)
        
        return {
            'success': True,
            'message': f'Successfully scraped {scraped_count} IPOs from IPOWatch',
            'scraping_details': {
                'url': url,
                'table_class_targeted': 'wp-block-table is-style-regular',
                'table_found': target_table is not None,
                'fallback_used': target_table is None,
                'total_rows': len(rows) - 1 if 'rows' in locals() else 0,
                'successful_extractions': scraped_count
            },
            'sample_data': gmp_data[:3] if gmp_data else [],  # First 3 entries as sample
            'saved_to_file': saved,
            'file_path': 'test_gmp_scraping_' + datetime.now().strftime('%Y-%m-%d') + '.json',
            'total_ipos_found': len(gmp_data),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in test GMP scraping: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to scrape GMP data from IPOWatch',
            'timestamp': datetime.now().isoformat()
        }

def _extract_symbol_from_name(company_name: str) -> str:
    """Extract symbol from company name"""
    if not company_name:
        return 'UNKNOWN'
        
    # Remove common suffixes and extract symbol
    name = company_name.upper().strip()
    
    # Remove common words
    remove_words = ['LIMITED', 'LTD', 'PRIVATE', 'PVT', 'COMPANY', 'CORP', 'CORPORATION', 'INC']
    for word in remove_words:
        name = name.replace(word, '')
    
    # Clean and extract meaningful symbol
    name = re.sub(r'[^A-Z0-9\s]', '', name).strip()
    
    # Take first few words as symbol
    words = name.split()
    if len(words) >= 2:
        return ''.join(words[:2])[:12]
    elif len(words) == 1:
        return words[0][:12]
    else:
        return 'UNKNOWN'

def _extract_number_from_text(text: str) -> float:
    """Extract number from text like ₹25, 13.13%, etc."""
    if not text or text.strip() == '-' or text.strip() == '':
        return None
        
    try:
        # Remove currency symbols and extra characters
        clean_text = re.sub(r'[₹%,\s]', '', text.strip())
        
        # Handle negative numbers
        if clean_text.startswith('-'):
            return None  # Return None for negative/no GMP
        
        # Extract number
        number_match = re.search(r'[\d.]+', clean_text)
        if number_match:
            return float(number_match.group())
        
        return None
        
    except Exception:
        return None