#!/usr/bin/env python3
"""
Debug Frontend - Flask Web Application
Interactive interface for testing and debugging Phase 2
"""

from flask import Flask, render_template, jsonify, request, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
import sys
from pathlib import Path
import threading
import json
import tempfile
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from config.logging_config import setup_logging, get_logger
from core.cache_manager import CacheManager
from core.perplexity_client import PerplexityClient
from core.data_extractor import FinancialDataExtractor
from core.research_storage import ResearchStorage
from core.research_orchestrator import ResearchOrchestrator
from core.hybrid_data_source import HybridDataSource
from core.excel_generator import ExcelGenerator
from utils.excel_upload_handler import ExcelUploadHandler

app = Flask(__name__, 
            template_folder='frontend/templates',
            static_folder='frontend/static')
CORS(app)

# Configure upload settings
UPLOAD_FOLDER = Path(__file__).parent / 'data' / 'uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Setup logging
setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger('debug_frontend')

# Initialize components
cache = CacheManager(settings.CACHE_DIR)
storage = ResearchStorage(settings.RESEARCH_RESULTS_DIR)
extractor = FinancialDataExtractor()

# Initialize Perplexity client
client = PerplexityClient(
    api_key=settings.PERPLEXITY_API_KEY,
    rate_limit_rpm=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    cache_manager=cache,
    use_finance_domain=settings.PERPLEXITY_USE_FINANCE_DOMAIN,
    model=settings.PERPLEXITY_MODEL
)

# Initialize hybrid data source (Moneycontrol primary, Perplexity fallback)
hybrid_source = HybridDataSource(client)

orchestrator = ResearchOrchestrator(client, storage, extractor)
excel_upload_handler = ExcelUploadHandler()

# Global state for async operations
research_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'results': []
}

@app.route('/')
def index():
    """Main wizard interface"""
    return render_template('wizard.html')

@app.route('/dashboard')
def dashboard():
    """Legacy enterprise dashboard"""
    return render_template('dashboard.html')

@app.route('/debug')
def debug():
    """Debug interface"""
    return render_template('debug.html')

@app.route('/api/companies')
def get_companies():
    """Get list of available companies"""
    from config.company_config import company_config
    return jsonify({
        'companies': company_config.get_all_companies()
    })

@app.route('/api/companies/add', methods=['POST'])
def add_company():
    """Add a new company"""
    try:
        from config.company_config import company_config
        data = request.json
        
        name = data.get('name')
        slug = data.get('slug')
        code = data.get('code')
        sector = data.get('sector', 'computers-software')
        full_name = data.get('full_name')
        # Allow name-only additions: generate slug/code when missing
        if not name:
            return jsonify({
                'success': False,
                'error': 'Missing required field: name'
            }), 400

        # Generate slug if not provided
        import re
        if not slug:
            slug = re.sub(r'[^a-z0-9-]', '', name.lower().strip().replace(' ', '-'))
            if not slug:
                slug = name.lower().strip().replace(' ', '-')

        # Generate a short code if not provided
        if not code:
            # Attempt to build code from uppercase initials or first letters
            words = [w for w in re.split(r'[^A-Za-z0-9]+', name) if w]
            if len(words) == 0:
                base = re.sub(r'[^A-Za-z0-9]', '', name)[:4].upper()
            elif len(words) == 1:
                base = re.sub(r'[^A-Za-z0-9]', '', words[0])[:4].upper()
            else:
                # use first letters of first up to 4 words
                initials = ''.join(w[0] for w in words)[:4]
                base = re.sub(r'[^A-Za-z0-9]', '', initials).upper()

            # Ensure uniqueness by appending numeric suffix if needed
            existing_codes = {cfg.get('code') for cfg in company_config.companies.values()}
            code_candidate = base
            suffix = 1
            while code_candidate in existing_codes:
                code_candidate = f"{base}{suffix}"
                suffix += 1
            code = code_candidate
        
        success = company_config.add_company(name, slug, code, sector, full_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Company {name} added successfully',
                'companies': company_config.get_all_companies()
            })
        else:
            # Company already existed - treat as idempotent success so the
            # frontend can decide how to include it in the current session.
            return jsonify({
                'success': True,
                'already_exists': True,
                'message': f'Company {name} already exists',
                'companies': company_config.get_all_companies()
            })
            
    except Exception as e:
        logger.error(f"Add company failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/companies/remove', methods=['POST'])
def remove_company():
    """Remove a company"""
    try:
        from config.company_config import company_config
        data = request.json
        name = data.get('name')
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Missing company name'
            }), 400
        
        success = company_config.remove_company(name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Company {name} removed successfully',
                'companies': company_config.get_all_companies()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Cannot remove company {name} (not found or is default)'
            }), 400
            
    except Exception as e:
        logger.error(f"Remove company failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/research/<company>/<quarter>/<int:year>', methods=['POST'])
def research_company(company, quarter, year):
    """Trigger research for a company using hybrid source"""
    try:
        logger.info(f"API request: Research {company} {quarter} {year}")
        
        # Use hybrid source (Perplexity primary, Moneycontrol fallback)
        result = hybrid_source.extract_financial_data(company, quarter, year)
        
        # Save to storage for persistence
        if result.get('extracted_data'):
            research_data = {
                'company': company,
                'quarter': quarter,
                'year': year,
                'status': 'success',
                'source': result.get('source', 'Unknown'),
                'extracted_data': result.get('extracted_data', {}),
                'context_confidence': result.get('context_confidence', 0),
                'raw_response': result.get('raw_response', ''),
                'is_fallback': result.get('is_fallback', False),
                'fallback_message': result.get('fallback_message', ''),
                'primary_source_failed': result.get('primary_source_failed', ''),
                'research_timestamp': datetime.now().isoformat()
            }
            storage.save_research(research_data)
            
            return jsonify({
                'success': True,
                'data': research_data
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'No data extracted'),
                'data': result
            })
    except Exception as e:
        logger.error(f"Research failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/research/batch', methods=['POST'])
def batch_research():
    """Batch research for multiple companies using hybrid source"""
    try:
        data = request.json
        companies = data.get('companies', [])
        quarters = data.get('quarters', ['Q1', 'Q2', 'Q3', 'Q4'])
        year = data.get('year', 2024)
        
        def run_research():
            global research_status
            research_status['running'] = True
            research_status['progress'] = 0
            research_status['message'] = 'Starting research...'
            research_status['results'] = []
            
            total = len(companies) * len(quarters)
            completed = 0
            
            for company in companies:
                for quarter in quarters:
                    try:
                        research_status['message'] = f'Researching {company} {quarter}...'
                        
                        # Use hybrid source
                        result = hybrid_source.extract_financial_data(company, quarter, year)
                        
                        # Save to storage
                        if result.get('extracted_data'):
                            research_data = {
                                'company': company,
                                'quarter': quarter,
                                'year': year,
                                'status': 'success',
                                'source': result.get('source', 'Unknown'),
                                'extracted_data': result.get('extracted_data', {}),
                                'context_confidence': result.get('context_confidence', 0),
                                'is_fallback': result.get('is_fallback', False),
                                'fallback_message': result.get('fallback_message', ''),
                                'primary_source_failed': result.get('primary_source_failed', ''),
                                'research_timestamp': datetime.now().isoformat()
                            }
                            storage.save_research(research_data)
                            research_status['results'].append(research_data)
                        
                        completed += 1
                        research_status['progress'] = int((completed / total) * 100)
                        
                    except Exception as e:
                        logger.error(f"Error researching {company} {quarter}: {e}")
                        completed += 1
                        research_status['progress'] = int((completed / total) * 100)
            
            research_status['running'] = False
            research_status['progress'] = 100
            research_status['message'] = 'Complete'
        
        # Start in background
        thread = threading.Thread(target=run_research)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Research started'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/research/status')
def research_status_endpoint():
    """Get current research status"""
    if orchestrator.progress_tracker:
        summary = orchestrator.progress_tracker.get_summary()
        return jsonify(summary)
    return jsonify(research_status)

@app.route('/api/results')
def get_results():
    """Get all research results"""
    try:
        all_results = storage.get_all_research()
        summary = storage.get_research_summary()
        
        return jsonify({
            'success': True,
            'summary': summary,
            'results': all_results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/results/<company>/<quarter>/<int:year>')
def get_result(company, quarter, year):
    """Get specific research result"""
    try:
        result = storage.load_research(company, quarter, year)
        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cache/stats')
def cache_stats():
    """Get cache statistics"""
    return jsonify(cache.get_stats())

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear API cache"""
    try:
        cache.clear()
        return jsonify({
            'success': True,
            'message': 'Cache cleared'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    return jsonify({
        'model': settings.PERPLEXITY_MODEL,
        'finance_domain': settings.PERPLEXITY_USE_FINANCE_DOMAIN,
        'rate_limit_rpm': settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        'cache_enabled': settings.CACHE_ENABLED,
        'cache_ttl': settings.CACHE_TTL_SECONDS,
        'api_key_set': bool(settings.PERPLEXITY_API_KEY)
    })

@app.route('/api/excel/upload', methods=['POST'])
def upload_excel():
    """Handle Excel file upload"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Secure the filename (for metadata only)
        filename = secure_filename(file.filename)

        # Save to a temporary file instead of persisting in uploads folder
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='_' + filename)
        tmp_path = Path(tmp.name)
        tmp.close()

        # Save incoming file to temp path
        file.save(str(tmp_path))
        logger.info(f"Temp file created: {tmp_path}")

        # Validate file
        is_valid, error_msg = excel_upload_handler.validate_file(tmp_path)
        if not is_valid:
            try:
                tmp_path.unlink()
            except Exception:
                pass
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        # Extract companies and file info
        companies = excel_upload_handler.extract_companies(tmp_path)
        file_info = excel_upload_handler.get_file_info(tmp_path)

        # Remove temporary file immediately to avoid storing uploads
        try:
            tmp_path.unlink()
            logger.info(f"Temp file deleted: {tmp_path}")
        except Exception:
            logger.warning(f"Could not delete temp file: {tmp_path}")

        return jsonify({
            'success': True,
            'original_filename': filename,
            'companies': companies,
            'company_count': len(companies),
            'file_info': file_info,
            'message': f'Successfully processed {filename} with {len(companies)} companies'
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/excel/parse/<path:filepath>', methods=['GET'])
def parse_excel(filepath):
    """Parse Excel file and extract companies"""
    try:
        file_path = Path(filepath)
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        # Extract companies
        companies = excel_upload_handler.extract_companies(file_path)
        
        # Get preview
        preview = excel_upload_handler.preview_data(file_path, max_rows=5)
        
        return jsonify({
            'success': True,
            'companies': companies,
            'company_count': len(companies),
            'preview': preview
        })
        
    except Exception as e:
        logger.error(f"Parse failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/excel/validate', methods=['POST'])
def validate_excel():
    """Validate Excel file format"""
    try:
        data = request.json
        filepath = Path(data.get('filepath'))
        
        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        is_valid, error_msg = excel_upload_handler.validate_file(filepath)
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'error': error_msg
        })
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/excel/generate', methods=['POST'])
def generate_excel():
    """Generate Excel file from all research results"""
    try:
        data = request.json or {}
        template_path = data.get('template_path')

        # Get all research results
        all_results = storage.get_all_research()
        
        if not all_results:
            return jsonify({
                'success': False,
                'error': 'No research data available'
            }), 400
        
        # Generate Excel
        generator = ExcelGenerator()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        output_path = Path(temp_file.name)
        temp_file.close()
        
        success = generator.generate_excel(all_results, output_path, template_path)
        
        if success:
            # Store filepath for download
            return jsonify({
                'success': True,
                'filepath': str(output_path),
                'filename': f'financial_research_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                'message': f'Generated Excel with {len(all_results)} research results'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate Excel file'
            }), 500
            
    except Exception as e:
        logger.error(f"Excel generation failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/excel/download/<path:filepath>')
def download_excel(filepath):
    """Download generated Excel file"""
    try:
        # Decode the filepath
        from urllib.parse import unquote
        from flask import Response
        import io
        
        file_path = Path(unquote(filepath))
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        filename = f'financial_research_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        logger.info(f"Sending file: {file_path} as {filename}")
        
        # Read file into memory
        with open(file_path, 'rb') as f:
            file_data = io.BytesIO(f.read())
        
        # Use send_file which handles headers and ranges robustness
        return send_file(
            file_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Financial Research Debug Frontend")
    print("="*60)
    print(f"\nAPI Key: {'✓ SET' if settings.PERPLEXITY_API_KEY else '✗ NOT SET'}")
    print(f"Finance Domain: {settings.PERPLEXITY_USE_FINANCE_DOMAIN}")
    print(f"Model: {settings.PERPLEXITY_MODEL}")
    print(f"Real-time Search: ✓ ENABLED (search_recency_filter=month)")
    print(f"Cache: {'✓ ENABLED' if settings.CACHE_ENABLED else '✗ DISABLED'}")
    print("\nStarting server at http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
