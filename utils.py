#!/usr/bin/env python3
"""
Shared utility functions for the HR Candidate Scorer application.
"""

import os
import json
import requests
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import google.generativeai as genai

PROMPTS = {}
try:
    with open('prompts.json', 'r') as f:
        PROMPTS = json.load(f)
except Exception as e:
    print(f"⚠️  Error loading prompts.json: {str(e)}")

def get_prompt(prompt_name, **kwargs):
    """Get and format a prompt from the loaded prompts."""
    prompt_template = PROMPTS.get(prompt_name, {}).get("prompt", "")
    return prompt_template.format(**kwargs)

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
                        
            except Exception as e:
                print(f"Could not extract {page_type} page: {str(e)}")
                continue
                
        return extracted_pages
        
    except Exception as e:
        print(f"Error extracting company pages: {str(e)}")
        return {}

def analyze_company_profile(company_website, model):
    """Comprehensive company analysis using web scraping + LLM"""
    if not company_website:
        return None
    
    try:
        # Extract company pages
        company_pages = extract_company_pages(company_website)
        
        if not company_pages:
            return None
        
        # Combine all extracted content
        combined_content = ""
        for page_type, content in company_pages.items():
            combined_content += f"\n--- {page_type.upper()} PAGE ---\n{content}\n"
        
        # Analyze with Gemini
        analysis_prompt = get_prompt(
            "analyze_company_profile",
            combined_content=combined_content[:8000]
        )
        
        response = model.generate_content(analysis_prompt)
        
        # Parse response
        try:
            cleaned_response = re.sub(r'```json\s*|\s*```', '', response.text).strip()
            company_profile = json.loads(cleaned_response)
            return company_profile
        except json.JSONDecodeError as e:
            print(f"Error decoding company analysis JSON: {e}")
            print(f"Raw response was: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error analyzing company profile: {str(e)}")
        return None
