#!/usr/bin/env python3
"""
Local test script for HR Candidate Scorer
Tests basic functionality without requiring full GCP setup
"""

import os
import sys
import tempfile
from unittest.mock import Mock, patch
import requests
import requests_mock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_url_extraction():
    """Test URL text extraction functionality"""
    print("Testing URL extraction...")
    
    # Import the function from main.py
    from main import extract_text_from_url
    
    # Mock the network call
    with requests_mock.Mocker() as m:
        m.get("https://httpbin.org/html", text="<html><body><h1>Herman Melville</h1></body></html>")
    
        # Test with a simple URL (using a test page)
        try:
            text = extract_text_from_url("https://httpbin.org/html")
            if text and "Herman Melville" in text:
                print("✅ URL extraction working")
                return True
            else:
                print("❌ URL extraction returned unexpected text")
                return False
        except Exception as e:
            print(f"❌ URL extraction failed: {e}")
            return False

def test_flask_app():
    """Test Flask app startup"""
    print("Testing Flask app initialization...")
    
    try:
        # Mock the GCP components that require authentication
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel'), \
             patch('google.cloud.documentai.DocumentProcessorServiceClient'):
            
            from main import app
            
            # Test that the app can be created
            with app.test_client() as client:
                response = client.get('/')
                if response.status_code == 200:
                    print("✅ Flask app starts successfully")
                    return True
                else:
                    print(f"❌ Flask app returned status {response.status_code}")
                    return False
                    
    except Exception as e:
        print(f"❌ Flask app failed to start: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies can be imported"""
    print("Testing dependencies...")
    
    required_modules = [
        'flask',
        'requests', 
        'bs4',
        'google.cloud.documentai',
        'google.generativeai'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            missing.append(module)
    
    return len(missing) == 0

def test_file_structure():
    """Test that all required files exist"""
    print("Testing file structure...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'Dockerfile',
        'deploy.sh',
        'templates/index.html'
    ]
    
    missing = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing.append(file_path)
    
    return len(missing) == 0

def main():
    """Run all tests"""
    print("🧪 HR Candidate Scorer - Local Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies), 
        ("Flask App", test_flask_app),
        ("URL Extraction", test_url_extraction)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your application is ready for deployment.")
        print("\nNext steps:")
        print("1. Set up GCP credentials: export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json")
        print("2. Get Document AI processor ID from GCP Console")
        print("3. Run locally: python main.py")
        print("4. Or deploy: ./deploy.sh")
    else:
        print(f"\n⚠️  Some tests failed. Please fix the issues before deploying.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
