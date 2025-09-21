# IPO Tracker API v2.0

Advanced IPO tracking and market analysis API with NSE data scraping, Gray Market Premium (GMP) analysis, and comprehensive market insights.

## Features

- ✅ Real-time IPO data from NSE
- ✅ Anti-blocking web scraping with CloudFlare bypass
- ✅ Gray Market Premium (GMP) tracking and analysis
- ✅ Market indices and sentiment analysis
- ✅ Current, upcoming & past IPOs
- ✅ Investment recommendations based on GMP
- ✅ RESTful API endpoints with comprehensive documentation
- ✅ Auto-retry mechanisms and fallback data
- ✅ Rate limiting protection
- ✅ Comprehensive error handling

## Quick Start

### 1. Install Dependencies

**Option A: Essential Only (Recommended)**
```bash
pip install fastapi uvicorn requests beautifulsoup4 lxml python-dateutil
```

**Option B: Full Features**
```bash
pip install -r requirements-minimal.txt
```

**Option C: Advanced Anti-blocking**
```bash
pip install -r requirements.txt
```

### 2. Run the Server
```bash
python start_server.py
```

### 3. Access the API
- **API Base**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### 🏠 Core Endpoints
- `GET /` - API information and status
- `GET /health` - Health check
- `GET /test` - System connectivity test
- `GET /docs` - Interactive API documentation

### 📈 IPO Endpoints
- `GET /api/ipo/current` - Current active IPOs
- `GET /api/ipo/upcoming` - Upcoming IPOs
- `GET /api/ipo/past?days_back=30` - Past IPOs
- `GET /api/ipo/summary` - Complete IPO summary
- `GET /api/ipo/search?query=company` - Search IPOs
- `GET /api/ipo/analytics` - IPO market analytics
- `GET /api/ipo/test` - Test IPO endpoints

### 💰 GMP (Gray Market Premium) Endpoints
- `GET /api/ipo/gmp` - GMP data for all IPOs
- `GET /api/ipo/gmp/recommendation/{company}` - GMP-based recommendations

### 📊 Market Endpoints
- `GET /api/market/indices` - Major market indices
- `GET /api/market/status` - Market status
- `GET /api/market/sentiment` - Market sentiment analysis
- `GET /api/market/overview` - Market overview
- `GET /api/market/dashboard` - Complete market dashboard
- `GET /api/market/test` - Test market endpoints

## Query Parameters

### IPO Endpoints
- `include_gmp=true` - Include Gray Market Premium data
- `days_back=30` - Number of days to look back (1-90)
- `query=company` - Search term for company name/symbol
- `category=all` - IPO category (current/upcoming/past/all)

### Examples

```bash
# Get current IPOs with GMP data
curl "http://localhost:8000/api/ipo/current?include_gmp=true"

# Search for energy companies
curl "http://localhost:8000/api/ipo/search?query=energy&category=current"

# Get past 7 days IPOs
curl "http://localhost:8000/api/ipo/past?days_back=7"

# Get complete analytics with GMP
curl "http://localhost:8000/api/ipo/analytics?include_gmp=true"

# Get GMP recommendation for specific company
curl "http://localhost:8000/api/ipo/gmp/recommendation/DEMO%20COMPANY"
```

## Response Format

All API responses follow a standard format:

```json
{
  "success": true,
  "message": "Successfully fetched data",
  "count": 5,
  "data": [...],
  "timestamp": "2025-09-21T10:30:00Z",
  "source": "NSE API + GMP Sources"
}
```

## Sample Responses

### Current IPOs
```json
{
  "success": true,
  "message": "Successfully fetched 2 current IPOs",
  "count": 2,
  "data": [
    {
      "symbol": "DEMO_CURRENT",
      "company_name": "Demo Current IPO Limited",
      "series": "EQ",
      "issue_start_date": "21-Sep-2025",
      "issue_end_date": "23-Sep-2025",
      "issue_price": "Rs.100 to Rs.120",
      "issue_size": "50000000",
      "status": "Active",
      "subscription_times": "1.25",
      "shares_offered": "5000000",
      "shares_bid": "6250000",
      "gmp": 85,
      "estimated_listing_gain": 70.8,
      "risk_level": "Low"
    }
  ],
  "gmp_included": true,
  "gmp_count": 3,
  "timestamp": "2025-09-21T10:30:00Z",
  "source": "NSE API + GMP Sources"
}
```

### Market Dashboard
```json
{
  "success": true,
  "message": "Market dashboard data fetched successfully",
  "dashboard": {
    "market_status": [
      {
        "market": "Capital Market",
        "marketStatus": "Open",
        "tradeDate": "21-Sep-2025",
        "index": "NIFTY 50"
      }
    ],
    "major_indices": [
      {
        "index_name": "NIFTY 50",
        "last": 25327.05,
        "open": 25410.2,
        "high": 25428.75,
        "low": 25286.3,
        "previous_close": 25423.6,
        "change": -96.55,
        "percent_change": -0.38,
        "year_high": 26277.35,
        "year_low": 21743.65
      }
    ],
    "market_sentiment": "neutral",
    "sentiment_score": 52.3
  }
}
```

## Postman Collection

Import the provided Postman collection for complete API testing:
- **File**: `IPO_Tracker_API_v2.0_Complete.postman_collection.json`
- **Features**: 50+ pre-configured requests with tests
- **Test Suites**: Health checks, data quality, performance, error handling
- **Automation**: Daily monitoring and system health checks

### Postman Collection Features
- 🏠 Health & Status tests
- 🧪 System connectivity tests  
- 📈 Complete IPO endpoint coverage
- 💰 GMP data and recommendations
- 📊 Market analysis endpoints
- ⚡ Performance testing
- ❌ Error handling validation
- 🔄 Data flow automation
- 📊 Data quality checks

## Configuration

### Environment Variables (.env)
```env
DEBUG=True
LOG_LEVEL=INFO
API_VERSION=2.0.0

# NSE API Settings
NSE_BASE_URL=https://www.nseindia.com/api
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT_DELAY=2

# Server Settings
HOST=0.0.0.0
PORT=8000
```

## Anti-blocking Features

The API includes advanced anti-blocking mechanisms:

1. **CloudScraper Integration** - Bypasses CloudFlare protection
2. **Multiple User Agents** - Rotates user agents to avoid detection
3. **Rate Limiting** - Intelligent delays between requests
4. **Session Management** - Maintains cookies and session state
5. **Retry Logic** - Automatic retries with exponential backoff
6. **Fallback Data** - Demo data when APIs are unavailable

## Data Sources

### NSE API Endpoints
- Current IPOs: `/api/ipo-current-issue`
- Upcoming IPOs: `/api/all-upcoming-issues`
- Past IPOs: `/api/public-past-issues`
- Market Indices: `/api/allIndices`
- Market Status: `/api/marketStatus`

### GMP Sources
- Multiple gray market premium data providers
- Real-time price tracking
- Investment recommendation algorithms

## Error Handling

The API provides comprehensive error handling:

- **Rate Limiting**: Automatic delays and retry logic
- **Network Errors**: Connection timeouts and retries
- **Data Validation**: Clean and validate all incoming data
- **Fallback Systems**: Demo data when sources are unavailable
- **Logging**: Detailed logs for debugging

## Logging

Logs are stored in the `logs/` directory:
- **File**: `logs/ipo_tracker.log`
- **Format**: Timestamp - Level - Message
- **Levels**: INFO, WARNING, ERROR
- **Rotation**: Automatic log rotation

## Dependencies

### Required
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing
- `pydantic` - Data validation

### Optional (Enhanced Features)
- `cloudscraper` - CloudFlare bypass
- `fake-useragent` - Dynamic user agents
- `python-dotenv` - Environment variables

## Development

### Project Structure
```
ipo_tracker/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── routers/             # API route handlers
│   │   ├── __init__.py
│   │   ├── ipo.py          # IPO endpoints
│   │   └── market.py       # Market endpoints
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   ├── nse_service.py  # NSE data fetching
│   │   ├── gmp_service.py  # GMP data processing
│   │   └── data_processor.py # Data processing
│   ├── models/             # Data models
│   │   ├── __init__.py
│   │   ├── ipo.py          # IPO models
│   │   └── market.py       # Market models
│   └── utils/              # Utilities
├── logs/                   # Log files
├── start_server.py         # Server startup script
├── requirements.txt        # Dependencies
└── README.md              # This file
```

### Running in Development Mode
```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the startup script
python start_server.py
```

## Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "start_server.py"]
```

### Production Settings
- Use `uvicorn` with multiple workers
- Enable proper logging configuration
- Set up reverse proxy (nginx)
- Configure SSL/TLS certificates
- Monitor with health checks

## Testing

### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Test all endpoints
curl http://localhost:8000/test

# Get current IPOs
curl http://localhost:8000/api/ipo/current
```

### Automated Testing
- Import Postman collection
- Run test suites for comprehensive validation
- Monitor API performance and data quality

## Support

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements-minimal.txt
   ```

2. **Port Already in Use**
   ```bash
   # Change port in start_server.py or kill existing process
   netstat -ano | findstr :8000
   ```

3. **NSE API Blocking**
   - API includes fallback demo data
   - Check logs for detailed error messages
   - Verify network connectivity

### Troubleshooting
- Check `logs/ipo_tracker.log` for detailed error messages
- Use `/test` endpoint to verify connectivity
- Monitor response times and success rates
- Enable DEBUG mode for verbose logging

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with proper testing
4. Update documentation
5. Submit pull request

## License

This project is for educational and research purposes. Please respect NSE's terms of service and rate limits.

---

**Version**: 2.0.0  
**Last Updated**: September 2025  
**Maintainer**: IPO Tracker Team