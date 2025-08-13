#!/usr/bin/env python3
"""
Simple test script to verify API endpoints are working
"""
import requests
import json
import sys

def test_endpoint(url, description):
    """Test a single endpoint"""
    try:
        print(f"\n🧪 Testing {description}")
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=5)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            print("   ✅ SUCCESS")
            return True
        else:
            print(f"   ❌ FAILED - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ FAILED - Connection Error: {e}")
        return False

def main():
    """Test all endpoints"""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing PastPort Data Processor API")
    print("=" * 50)
    
    endpoints = [
        (f"{base_url}/", "Root endpoint"),
        (f"{base_url}/api/v1/health", "Basic health check"),
        (f"{base_url}/api/v1/health/db", "Database health check"),
    ]
    
    results = []
    for url, description in endpoints:
        success = test_endpoint(url, description)
        results.append(success)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Total tests: {len(results)}")
    print(f"   Passed: {sum(results)}")
    print(f"   Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("   🎉 All tests passed!")
        return 0
    else:
        print("   ⚠️  Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
