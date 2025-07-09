#!/usr/bin/env python3
"""
Company Analysis Script for HR Candidate Scorer
Runs during deployment to analyze company profile once and save for reuse
"""

import os
import sys
import json
import google.generativeai as genai
from utils import analyze_company_profile

def main():
    """Main function to run company analysis"""
    
    # Get environment variables
    PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-pro')
    COMPANY_WEBSITE = os.environ.get('COMPANY_WEBSITE')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    if not PROJECT_ID:
        print("❌ GCP_PROJECT_ID environment variable is required")
        sys.exit(1)
    
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY environment variable is required")
        sys.exit(1)
    
    if not COMPANY_WEBSITE:
        print("ℹ️  No COMPANY_WEBSITE provided - skipping company analysis")
        sys.exit(0)
    
    try:
        print(f"🚀 Starting company analysis for: {COMPANY_WEBSITE}")
        print(f"📍 Project: {PROJECT_ID}")
        print(f"🤖 Model: {GEMINI_MODEL}")
        
        # Initialize Gemini API
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Analyze company profile using the utility function
        company_profile = analyze_company_profile(COMPANY_WEBSITE, model)
        
        if company_profile:
            # Save to file
            with open('company_profile.json', 'w') as f:
                json.dump(company_profile, f, indent=2)
            
            print("✅ Company profile saved to company_profile.json")
            
            # Print summary
            print("\n📊 Company Analysis Summary:")
            print(f"   Industry: {company_profile.get('business_intelligence', {}).get('industry_sector', 'N/A')}")
            print(f"   Stage: {company_profile.get('growth_stage', {}).get('stage', 'N/A')}")
            print(f"   Culture: {company_profile.get('company_culture', {}).get('work_environment', 'N/A')}")
            mission = company_profile.get('company_focus', {}).get('core_mission', 'N/A')
            print(f"   Mission: {mission[:100]}{'...' if len(mission) > 100 else ''}")
            
        else:
            print("❌ Failed to generate company profile")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
