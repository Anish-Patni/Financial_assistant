#!/usr/bin/env python3
"""
Flask API Validation Script
Tests the Flask API endpoints directly using HTTP requests
This validates that the Flask app is serving data correctly
"""

import requests
import json
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
OUTPUT_FILE = Path(__file__).parent / "api_validation_results.txt"

def log_both(f, message=""):
    """Log to both file and console"""
    print(message)
    f.write(message + "\n")
    f.flush()

def test_api():
    """Test all Flask API endpoints"""
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        log_both(f, "="*70)
        log_both(f, " FLASK API VALIDATION - HTTP Endpoint Testing")
        log_both(f, "="*70)
        log_both(f, f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log_both(f, f" Base URL: {BASE_URL}")
        log_both(f, "="*70)
        log_both(f)
        
        results = {}
        
        # Test 1: Check if server is running
        log_both(f, "="*70)
        log_both(f, " TEST 1: Server Health Check")
        log_both(f, "="*70)
        log_both(f)
        
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            if response.status_code == 200:
                log_both(f, "✓ Server is running and responding")
                log_both(f, f"✓ Status Code: {response.status_code}")
                results['server'] = True
            else:
                log_both(f, f"✗ Server returned status code: {response.status_code}")
                results['server'] = False
            log_both(f)
        except requests.exceptions.ConnectionError:
            log_both(f, "✗ FAILED: Cannot connect to server")
            log_both(f, "  Make sure Flask app is running on http://localhost:5000")
            results['server'] = False
            log_both(f)
        except Exception as e:
            log_both(f, f"✗ FAILED: {e}")
            results['server'] = False
            log_both(f)
        
        # If server is not running, stop here
        if not results['server']:
            log_both(f, "="*70)
            log_both(f, " STOPPING: Server is not running")
            log_both(f, "="*70)
            log_both(f)
            log_both(f, "Please start the Flask server with: python app.py")
            return False
        
        # Test 2: Get Companies
        log_both(f, "="*70)
        log_both(f, " TEST 2: API /api/companies")
        log_both(f, "="*70)
        log_both(f)
        
        try:
            response = requests.get(f"{BASE_URL}/api/companies", timeout=5)
            if response.status_code == 200:
                data = response.json()
                companies = data.get('companies', [])
                log_both(f, "✓ API endpoint responding")
                log_both(f, f"✓ Status Code: {response.status_code}")
                log_both(f, f"✓ Companies available: {len(companies)}")
                log_both(f)
                log_both(f, "Sample Companies:")
                for i, company in enumerate(companies[:5], 1):
                    log_both(f, f"  {i}. {company}")
                if len(companies) > 5:
                    log_both(f, f"  ... and {len(companies) - 5} more")
                results['companies'] = True
            else:
                log_both(f, f"✗ Failed with status: {response.status_code}")
                log_both(f, f"✗ Response: {response.text}")
                results['companies'] = False
            log_both(f)
        except Exception as e:
            log_both(f, f"✗ FAILED: {e}")
            results['companies'] = False
            log_both(f)
        
        # Test 3: Get Config
        log_both(f, "="*70)
        log_both(f, " TEST 3: API /api/config")
        log_both(f, "="*70)
        log_both(f)
        
        try:
            response = requests.get(f"{BASE_URL}/api/config", timeout=5)
            if response.status_code == 200:
                config = response.json()
                log_both(f, "✓ API endpoint responding")
                log_both(f, f"✓ Status Code: {response.status_code}")
                log_both(f)
                log_both(f, "Configuration:")
                log_both(f, f"  - Model: {config.get('model', 'N/A')}")
                log_both(f, f"  - Finance Domain: {config.get('finance_domain', 'N/A')}")
                log_both(f, f"  - Rate Limit: {config.get('rate_limit_rpm', 'N/A')} RPM")
                log_both(f, f"  - Cache Enabled: {config.get('cache_enabled', 'N/A')}")
                log_both(f, f"  - API Key Set: {config.get('api_key_set', 'N/A')}")
                results['config'] = True
            else:
                log_both(f, f"✗ Failed with status: {response.status_code}")
                results['config'] = False
            log_both(f)
        except Exception as e:
            log_both(f, f"✗ FAILED: {e}")
            results['config'] = False
            log_both(f)
        
        # Test 4: Get Results (MOST IMPORTANT)
        log_both(f, "="*70)
        log_both(f, " TEST 4: API /api/results (CRITICAL TEST)")
        log_both(f, "="*70)
        log_both(f)
        
        try:
            response = requests.get(f"{BASE_URL}/api/results", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                summary = data.get('summary', {})
                all_results = data.get('results', [])
                
                log_both(f, "✓ API endpoint responding")
                log_both(f, f"✓ Status Code: {response.status_code}")
                log_both(f, f"✓ Success: {success}")
                log_both(f)
                log_both(f, "Results Summary:")
                log_both(f, f"  - Total Results: {len(all_results)}")
                log_both(f, f"  - Companies: {len(summary.get('companies', []))}")
                log_both(f, f"  - Quarters: {summary.get('quarters', [])}")
                log_both(f, f"  - Years: {summary.get('years', [])}")
                log_both(f)
                
                if all_results:
                    log_both(f, "✓ BACKEND IS RETURNING DATA!")
                    log_both(f)
                    log_both(f, "Sample Results (first 5):")
                    for i, res in enumerate(all_results[:5], 1):
                        company = res.get('company', 'N/A')
                        quarter = res.get('quarter', 'N/A')
                        year = res.get('year', 'N/A')
                        status = res.get('status', 'N/A')
                        data_count = len(res.get('data', {}))
                        log_both(f, f"  {i}. {company} | {quarter} {year} | Status: {status} | Data Points: {data_count}")
                    
                    if len(all_results) > 5:
                        log_both(f, f"  ... and {len(all_results) - 5} more results")
                    
                    log_both(f)
                    log_both(f, "✓ Full JSON Response Sample:")
                    log_both(f, json.dumps(all_results[0], indent=2)[:500] + "...")
                    
                    results['results'] = True
                else:
                    log_both(f, "⚠ WARNING: API responds but returns NO data")
                    log_both(f, "  This means research results exist but aren't being loaded")
                    results['results'] = False
            else:
                log_both(f, f"✗ Failed with status: {response.status_code}")
                log_both(f, f"✗ Response: {response.text}")
                results['results'] = False
            log_both(f)
        except Exception as e:
            log_both(f, f"✗ FAILED: {e}")
            import traceback
            log_both(f, traceback.format_exc())
            results['results'] = False
            log_both(f)
        
        # Test 5: Get Cache Stats
        log_both(f, "="*70)
        log_both(f, " TEST 5: API /api/cache/stats")
        log_both(f, "="*70)
        log_both(f)
        
        try:
            response = requests.get(f"{BASE_URL}/api/cache/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                log_both(f, "✓ API endpoint responding")
                log_both(f, f"✓ Status Code: {response.status_code}")
                log_both(f, f"✓ Cache Stats: {stats}")
                results['cache'] = True
            else:
                log_both(f, f"✗ Failed with status: {response.status_code}")
                results['cache'] = False
            log_both(f)
        except Exception as e:
            log_both(f, f"✗ FAILED: {e}")
            results['cache'] = False
            log_both(f)
        
        # Test 6: Research Status
        log_both(f, "="*70)
        log_both(f, " TEST 6: API /api/research/status")
        log_both(f, "="*70)
        log_both(f)
        
        try:
            response = requests.get(f"{BASE_URL}/api/research/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                log_both(f, "✓ API endpoint responding")
                log_both(f, f"✓ Status Code: {response.status_code}")
                log_both(f, f"✓ Research Status: {status}")
                results['status'] = True
            else:
                log_both(f, f"✗ Failed with status: {response.status_code}")
                results['status'] = False
            log_both(f)
        except Exception as e:
            log_both(f, f"✗ FAILED: {e}")
            results['status'] = False
            log_both(f)
        
        # Summary
        log_both(f, "="*70)
        log_both(f, " TEST SUMMARY")
        log_both(f, "="*70)
        log_both(f)
        
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            log_both(f, f"{status} | {test_name.upper()}")
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        log_both(f)
        log_both(f, "="*70)
        log_both(f, f" Total: {passed}/{total} tests passed")
        log_both(f, "="*70)
        log_both(f)
        
        if passed == total:
            log_both(f, "✓ ALL API TESTS PASSED!")
            log_both(f)
            log_both(f, "CONCLUSION:")
            log_both(f, "  The Flask API is working correctly and returning data.")
            log_both(f, "  Since you're not seeing output in the frontend, the issue is")
            log_both(f, "  definitely in the FRONTEND JavaScript code:")
            log_both(f)
            log_both(f, "  Possible issues:")
            log_both(f, "    1. Frontend not making API calls at all")
            log_both(f, "    2. Frontend making calls to wrong URL")
            log_both(f, "    3. Frontend not handling the response correctly")
            log_both(f, "    4. Frontend not displaying the data (DOM manipulation issue)")
            log_both(f, "    5. JavaScript errors preventing execution (check browser console)")
            log_both(f)
            log_both(f, "  Next steps:")
            log_both(f, "    - Open browser Developer Tools (F12)")
            log_both(f, "    - Check Console for JavaScript errors")
            log_both(f, "    - Check Network tab to see if API calls are being made")
            log_both(f, "    - Verify responses in Network tab match expected data")
        elif results.get('results', False):
            log_both(f, "✓ CRITICAL TEST PASSED - API Returns Data!")
            log_both(f)
            log_both(f, "  The /api/results endpoint is working and returning data.")
            log_both(f, "  The issue is in the FRONTEND code.")
        else:
            log_both(f, "✗ API NOT RETURNING DATA!")
            log_both(f)
            log_both(f, "CONCLUSION:")
            log_both(f, "  The Flask API is running but not returning research results.")
            log_both(f, "  This could be a backend storage or routing issue.")
            log_both(f, "  Review the Flask app logs for errors.")
        
        log_both(f)
        log_both(f, f"Full results saved to: {OUTPUT_FILE}")
        log_both(f)
        
        return passed == total

if __name__ == '__main__':
    try:
        print("\nStarting Flask API Validation...")
        print(f"Testing endpoints at: {BASE_URL}")
        print("=" * 70)
        print()
        
        success = test_api()
        
        print("\n" + "=" * 70)
        print(f"✓ Results saved to: {OUTPUT_FILE}")
        print("=" * 70)
        print()
        
        if success:
            print("✅ ALL TESTS PASSED - Backend API is working correctly!")
        else:
            print("⚠️  SOME TESTS FAILED - Review results file for details")
        
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
