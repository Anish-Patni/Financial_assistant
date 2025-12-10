# AI-Powered Financial Research Engine

**Phase 1: Foundation & Research Infrastructure - COMPLETE**

An automated financial research platform that extracts, processes, and validates financial data for IT services companies using AI-powered research via the Perplexity API.

## 🎯 Project Overview

This application automates the extraction of quarterly financial data for Indian IT companies, performs sophisticated calculations, validates data quality, and generates comprehensive Excel reports - all powered by AI research capabilities.

## 📋 Phase 1 Features (IMPLEMENTED)

✅ **Project Infrastructure**
- Modular Python architecture
- Environment-based configuration
- Professional logging system with rotation

✅ **Perplexity API Integration**
- Complete API wrapper with authentication
- Token bucket rate limiting (prevents API throttling)
- Exponential backoff retry logic
- Intelligent caching system (reduces API costs)
- Financial query templates

✅ **Financial Data Engine**
- Comprehensive data models for 25+ indicators
- Automatic calculation of derived metrics:
  - Contribution, EBITDA, EBIT, PBT, PAT
  - Margin percentages
  - Year-over-year growth
- Data completeness tracking

✅ **Validation System**
- Range validation (detect outliers)
- Consistency checks (verify calculations)
- Trend analysis (QoQ change detection)
- Margin reasonability checks

✅ **Excel Processing**
- Template parsing and validation
- Company name extraction
- Quarterly data extraction
- Sample template generation

## 🚀 Quick Start

### Installation

1. **Install Dependencies**
```bash
cd financial-research-app
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
# Copy example environment file
copy .env.example .env

# Edit .env and add your Perplexity API key
# PERPLEXITY_API_KEY=your_actual_api_key_here
```

3. **Run Verification**
```bash
python verify_phase1.py
```

## 📁 Project Structure

```
financial-research-app/
├── config/                  # Configuration management
│   ├── settings.py         # Central settings
│   └── logging_config.py   # Logging setup
├── core/                   # Core business logic
│   ├── perplexity_client.py  # API integration
│   ├── data_models.py      # Financial data structures
│   └── cache_manager.py    # Caching system
├── parsers/               # Data parsing
│   └── excel_parser.py    # Excel file processing
├── utils/                 # Utilities
│   └── validators.py      # Data validation
├── tests/                 # Test suite
├── data/                  # Data storage
│   ├── templates/         # Excel templates
│   └── cache/            # API cache
├── logs/                  # Application logs
├── verify_phase1.py       # Verification script
├── requirements.txt       # Dependencies
└── .env.example          # Environment template
```

## 🔧 Configuration

All configuration is managed through environment variables in `.env`:

```bash
# API Configuration
PERPLEXITY_API_KEY=your_key
PERPLEXITY_MODEL=llama-3.1-sonar-large-128k-online

# Rate Limiting
RATE_LIMIT_RPM=20          # Requests per minute
RATE_LIMIT_TPM=10000       # Tokens per minute

# Cache Settings
CACHE_ENABLED=true
CACHE_TTL_SECONDS=86400    # 24 hours

# Logging
LOG_LEVEL=INFO
```

## 💡 Usage Examples

### Example 1: Query Financial Data

```python
from core.perplexity_client import PerplexityClient
from core.cache_manager import CacheManager
from config import settings

# Initialize
cache = CacheManager(settings.CACHE_DIR)
client = PerplexityClient(
    api_key=settings.PERPLEXITY_API_KEY,
    cache_manager=cache
)

# Get company financials
data = client.get_company_financials('TCS', 'Q1', 2024)
print(data)
```

### Example 2: Parse Excel Template

```python
from parsers.excel_parser import ExcelParser

# Load and parse
parser = ExcelParser('path/to/template.xlsx')
parser.load_file()

# Extract companies
companies = parser.extract_companies_from_sheet()
print(f"Found companies: {companies}")

parser.close()
```

### Example 3: Calculate Financial Metrics

```python
from core.data_models import QuarterlyData

# Create quarterly data
q_data = QuarterlyData(
    company='TCS',
    quarter='Q1',
    year=2024,
    total_income=5000.0,
    employee_cost=3000.0,
    other_expenses=500.0,
    # ... other fields
)

# Auto-calculate derived metrics
q_data.calculate_derived_metrics()

print(f"EBITDA: {q_data.op_ebitda}")
print(f"EBITDA Margin: {q_data.op_ebitda_pct}%")
```

### Example 4: Validate Data

```python
from utils.validators import FinancialValidator

validator = FinancialValidator()
is_valid, report = validator.validate_quarterly_data(q_data)

print(f"Status: {report['status']}")
print(f"Completeness: {report['completeness']}%")
print(f"Errors: {report['errors']}")
```

## 📊 Verification Tests

The `verify_phase1.py` script runs 8 comprehensive tests:

1. ✅ Configuration & Setup
2. ✅ Logging System
3. ✅ Cache Manager
4. ✅ Data Models & Calculations
5. ✅ Validation Engine
6. ✅ Excel Parser
7. ✅ Perplexity API Client
8. ✅ End-to-End Workflow

## 🎯 Supported Financial Indicators

**Core Metrics:**
- Total Income from Operations
- Purchase of Traded Goods
- Stock Changes
- Employee Cost
- Other Expenses
- Depreciation
- Interest
- Other Income
- Tax

**Calculated Metrics:**
- Contribution
- Operating EBITDA
- Operating EBIT
- Operating PBT
- PBT (Total)
- PAT
- All margin percentages

## 🔒 Features

- **Rate Limiting**: Prevents API throttling with token bucket algorithm
- **Caching**: Reduces API costs by caching responses (24h default TTL)
- **Retry Logic**: Exponential backoff for transient failures
- **Validation**: Multi-layer validation ensures data quality
- **Logging**: Comprehensive logging with rotation (10MB per file)
- **Error Handling**: Graceful error handling throughout

## 📈 Next Phases

**Phase 2** (Upcoming):
- Automated research for 13 companies
- Advanced NLP extraction patterns
- Historical data tracking
- Comparison analytics

**Phase 3** (Future):
- Dynamic Excel generation
- Beautiful formatting & charts
- Interactive preview interface
- Q&A capabilities

## 🐛 Troubleshooting

**API Key Issues:**
```bash
# Verify API key is set
python -c "from config import settings; print('OK' if settings.PERPLEXITY_API_KEY else 'Missing')"
```

**Module Import Errors:**
```bash
# Ensure you're in the project root
cd financial-research-app
python verify_phase1.py
```

**Cache Issues:**
```python
from core.cache_manager import CacheManager
from config import settings

cache = CacheManager(settings.CACHE_DIR)
cache.clear()  # Clear all cache
```

## 📝 Logging

Logs are stored in `logs/` directory:
- `financial_research.log` - All logs
- `errors.log` - Errors only

## 🤝 Contributing

This is Phase 1 of a multi-phase project. See `financial-research-roadmap.yaml` for the complete implementation plan.

## 📄 License

Internal project - NETSCIENCE TECHNOLOGIES PRIVATE LIMITED

---

**Status**: Phase 1 Complete ✅  
**Last Updated**: December 2025  
**Contact**: Development Team
