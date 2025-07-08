#!/usr/bin/env python3
"""
Company Analysis Script for HR Candidate Scorer
Runs during deployment to analyze company profile once and save for reuse
"""

import os
import sys
import json
import requests
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import google.generativeai as genai

def extract_company_pages(company_website):
    """Extract content from key company pages"""
    if not company_website:
        return {}
    
    try:
        parsed_url = urlparse(company_website)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Key pages to analyze
        pages_to_check = [
            ('main', company_website),
            ('about', urljoin(base_url, '/about')),
            ('about-us', urljoin(base_url, '/about-us')),
            ('careers', urljoin(base_url, '/careers')),
            ('jobs', urljoin(base_url, '/jobs')),
            ('team', urljoin(base_url, '/team')),
            ('culture', urljoin(base_url, '/culture')),
            ('values', urljoin(base_url, '/values')),
            ('mission', urljoin(base_url, '/mission')),
            ('news', urljoin(base_url, '/news')),
            ('blog', urljoin(base_url, '/blog'))
        ]
        
        extracted_pages = {}
        
        for page_type, url in pages_to_check:
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    
                    text = soup.get_text()
                    # Clean up whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    if len(text) > 200:  # Only include meaningful content
                        extracted_pages[page_type] = text[:2000]  # Limit content length
                        print(f"✅ Extracted {page_type} page ({len(text)} chars)")
                        
            except Exception as e:
                print(f"⚠️  Could not extract {page_type} page: {str(e)}")
                continue
                
        return extracted_pages
        
    except Exception as e:
        print(f"❌ Error extracting company pages: {str(e)}")
        return {}

def analyze_company_profile(company_website, model):
    """Comprehensive company analysis using web scraping + LLM"""
    if not company_website:
        return None
    
    try:
        print(f"🌐 Analyzing company website: {company_website}")
        
        # Extract company pages
        company_pages = extract_company_pages(company_website)
        
        if not company_pages:
            print("❌ No company pages could be extracted")
            return None
        
        print(f"📄 Successfully extracted {len(company_pages)} company pages")
        
        # Combine all extracted content
        combined_content = ""
        for page_type, content in company_pages.items():
            combined_content += f"\n--- {page_type.upper()} PAGE ---\n{content}\n"
        
        print(f"🧠 Analyzing company content with AI ({len(combined_content)} chars)...")
        
        # Analyze with Gemini
        analysis_prompt = f"""
        Analyze the following company information and provide a comprehensive company profile.
        
        COMPANY CONTENT:
        {combined_content[:8000]}  # Limit content to avoid token limits
        
        Provide analysis in JSON format:
        {{
            "business_intelligence": {{
                "industry_sector": "string",
                "business_model": "string", 
                "products_services": ["service1", "service2"],
                "target_markets": ["market1", "market2"]
            }},
            "company_focus": {{
                "core_mission": "string",
                "strategic_priorities": ["priority1", "priority2"],
                "values": ["value1", "value2"]
            }},
            "geographic_presence": {{
                "headquarters": "string",
                "offices": ["location1", "location2"],
                "market_focus": "string"
            }},
            "company_culture": {{
                "work_environment": "string",
                "leadership_style": "string",
                "team_dynamics": "string",
                "communication_style": "string"
            }},
            "work_preferences": {{
                "remote_policy": "string",
                "collaboration_tools": ["tool1", "tool2"],
                "work_life_balance": "string"
            }},
            "growth_stage": {{
                "stage": "startup/scale-up/enterprise",
                "funding_status": "string",
                "expansion_plans": "string"
            }},
            "technical_culture": {{
                "technologies_used": ["tech1", "tech2"],
                "innovation_focus": "string",
                "technical_approach": "string"
            }},
            "market_position": {{
                "competitors": ["comp1", "comp2"],
                "market_share": "string",
                "reputation": "string"
            }}
        }}
        """
        
        response = model.generate_content(analysis_prompt)
        
        # Parse response
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            json_str = match.group(0)
            company_profile = json.loads(json_str)
            print("✅ Company profile analysis completed successfully")
            return company_profile
        else:
            print(f"❌ Could not parse company analysis response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error analyzing company profile: {str(e)}")
        return None

def main():
    """Main function to run company analysis"""
    
    # Get environment variables
    PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
    REGION = os.environ.get('GCP_REGION', 'us-central1')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-pro')
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
        
        # Analyze company profile
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
