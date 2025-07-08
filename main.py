import os
import requests
import tempfile
import json
import re
import time
from flask import Flask, request, render_template, jsonify
from google.cloud import documentai
import google.generativeai as genai
import PyPDF2
import io
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# Load configuration from environment variables
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
REGION = os.environ.get('GCP_REGION', 'us-central1')
LOCATION = os.environ.get('GCP_LOCATION', 'us')
PROCESSOR_ID = os.environ.get('DOCUMENT_AI_PROCESSOR_ID')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-pro')
COMPANY_WEBSITE = os.environ.get('COMPANY_WEBSITE')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID environment variable is required")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# Load pre-analyzed company profile (generated during deployment)
COMPANY_PROFILE = None
try:
    if os.path.exists('company_profile.json'):
        with open('company_profile.json', 'r') as f:
            COMPANY_PROFILE = json.load(f)
        print(f"✅ Loaded company profile for enhanced analysis")
    else:
        print("ℹ️  No company profile found - using basic scoring")
except Exception as e:
    print(f"⚠️  Error loading company profile: {str(e)} - using basic scoring")

def extract_text_from_pdf(pdf_content):
    """Extract text from PDF using Document AI or fallback to PyPDF2"""
    if PROCESSOR_ID:
        try:
            # Use Document AI if processor ID is available
            client = documentai.DocumentProcessorServiceClient()
            name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
            
            raw_document = documentai.RawDocument(content=pdf_content, mime_type="application/pdf")
            request_doc = documentai.ProcessRequest(name=name, raw_document=raw_document)
            
            result = client.process_document(request=request_doc)
            return result.document.text
        except Exception as e:
            print(f"Document AI failed, falling back to PyPDF2: {str(e)}")
    
    # Fallback to PyPDF2 if Document AI is not available
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"PyPDF2 extraction failed: {str(e)}")
        return ""

def extract_text_from_url(url):
    """New: Extract JD from URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Simple text extraction (can enhance with BeautifulSoup if needed)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        return soup.get_text()
    except Exception as e:
        return f"Error extracting from URL: {str(e)}"

def analyze_resume(resume_text):
    """Reuse existing Gemini prompts from backup system"""
    prompt = f"""
    Extract the name, email, and skills from the following resume text.
    Return ONLY a valid JSON object with the keys "name", "email", "phone", "skills", "experience_years", "experience_level", and "summary".
    Do not include any other text or formatting.

    Resume Text:
    {resume_text}
    """
    
    response = model.generate_content(prompt)
    return response.text

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

def analyze_company_profile(company_website):
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
            return company_profile
        else:
            print(f"Could not parse company analysis response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error analyzing company profile: {str(e)}")
        return None

def score_candidate_with_company_context(resume_data, jd_text, company_profile=None):
    """Enhanced scoring with comprehensive company context"""
    
    if company_profile:
        # Enhanced scoring with company context
        prompt = f"""
        Score this candidate against the job description with comprehensive company context:

        CANDIDATE:
        {resume_data}

        JOB DESCRIPTION:
        {jd_text}

        COMPANY PROFILE:
        {json.dumps(company_profile, indent=2)}

        Consider the following multi-dimensional fit assessment:
        1. Technical Skills Alignment
        2. Experience Relevance 
        3. Industry & Business Model Fit
        4. Cultural & Work Style Compatibility
        5. Geographic & Market Alignment
        6. Growth Stage & Career Level Match
        7. Values & Mission Alignment
        8. Communication & Collaboration Style

        Provide comprehensive scoring in JSON format:
        {{
            "overall_score": 1-10,
            "skills_match": 1-10,
            "experience_match": 1-10,
            "culture_fit": 1-10,
            "industry_fit": 1-10,
            "geographic_fit": 1-10,
            "growth_stage_fit": 1-10,
            "values_alignment": 1-10,
            "recommendation": "Strong/Moderate/Weak Match",
            "strengths": ["strength1", "strength2", "strength3"],
            "concerns": ["concern1", "concern2"],
            "interview_focus": ["topic1", "topic2", "topic3"],
            "company_fit_highlights": ["highlight1", "highlight2"],
            "potential_challenges": ["challenge1", "challenge2"],
            "onboarding_considerations": ["consideration1", "consideration2"],
            "rationale": "3-4 sentence comprehensive explanation including company context"
        }}
        """
    else:
        # Fallback to basic scoring if no company profile
        prompt = f"""
        Score this candidate against the job description:

        CANDIDATE:
        {resume_data}

        JOB DESCRIPTION:
        {jd_text}

        Provide scoring in JSON format:
        {{
            "overall_score": 1-10,
            "skills_match": 1-10,
            "experience_match": 1-10,
            "culture_fit": 1-10,
            "recommendation": "Strong/Moderate/Weak Match",
            "strengths": ["strength1", "strength2"],
            "concerns": ["concern1", "concern2"],
            "interview_focus": ["topic1", "topic2"],
            "rationale": "2-3 sentence explanation"
        }}
        """
    
    response = model.generate_content(prompt)
    return response.text

def score_candidate(resume_data, jd_text):
    """Legacy function - maintained for backward compatibility"""
    return score_candidate_with_company_context(resume_data, jd_text, None)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get inputs
        jd_url = request.form.get('jd_url')
        resume_file = request.files.get('resume_file')
        
        if not jd_url or not resume_file:
            return jsonify({"error": "Please provide both JD URL and resume file"})
        
        print(f"Processing file: {resume_file.filename}")
        
        # Extract JD text
        jd_text = extract_text_from_url(jd_url)
        if jd_text.startswith("Error"):
            return jsonify({"error": jd_text})
        
        # Extract resume text
        resume_content = resume_file.read()
        if resume_file.filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(resume_content)
        else:
            resume_text = resume_content.decode('utf-8')
        
        if not resume_text:
            return jsonify({"error": f"Could not extract text from {resume_file.filename}"})
        
        # Analyze resume with JSON parsing like backup system
        try:
            resume_response = analyze_resume(resume_text)
            # Find the JSON object in the response text
            match = re.search(r'\{.*\}', resume_response, re.DOTALL)
            if match:
                json_str = match.group(0)
                resume_data = json.loads(json_str)
            else:
                print(f"Could not find a JSON object in the Gemini response: {resume_response}")
                return jsonify({"error": "Could not parse resume analysis response"})
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error decoding or parsing Gemini response: {resume_response if 'resume_response' in locals() else 'No response'}, Error: {str(e)}")
            return jsonify({"error": "Error parsing resume analysis"})
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            return jsonify({"error": f"Error analyzing resume: {str(e)}"})
        
        # Enhanced candidate scoring with pre-loaded company context
        try:
            scoring_response = score_candidate_with_company_context(
                json.dumps(resume_data), 
                jd_text, 
                COMPANY_PROFILE  # Use pre-loaded company profile
            )
            # Find the JSON object in the response text
            match = re.search(r'\{.*\}', scoring_response, re.DOTALL)
            if match:
                scoring_json_str = match.group(0)
                scoring_data = json.loads(scoring_json_str)
            else:
                print(f"Could not find a JSON object in the scoring response: {scoring_response}")
                return jsonify({"error": "Could not parse scoring response"})
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error decoding or parsing scoring response: {scoring_response if 'scoring_response' in locals() else 'No response'}, Error: {str(e)}")
            return jsonify({"error": "Error parsing scoring response"})
        except Exception as e:
            print(f"Error calling scoring API: {str(e)}")
            return jsonify({"error": f"Error scoring candidate: {str(e)}"})
        
        # Prepare response with enhanced data
        response_data = {
            "success": True,
            "resume_analysis": resume_data,
            "scoring": scoring_data,
            "jd_preview": jd_text[:500] + "..." if len(jd_text) > 500 else jd_text,
            "enhanced_analysis": COMPANY_PROFILE is not None
        }
        
        # Include company profile summary if available
        if COMPANY_PROFILE:
            response_data["company_summary"] = {
                "industry": COMPANY_PROFILE.get("business_intelligence", {}).get("industry_sector", "N/A"),
                "stage": COMPANY_PROFILE.get("growth_stage", {}).get("stage", "N/A"),
                "culture": COMPANY_PROFILE.get("company_culture", {}).get("work_environment", "N/A"),
                "mission": COMPANY_PROFILE.get("company_focus", {}).get("core_mission", "N/A")[:200] + "..." if len(COMPANY_PROFILE.get("company_focus", {}).get("core_mission", "")) > 200 else COMPANY_PROFILE.get("company_focus", {}).get("core_mission", "N/A")
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
