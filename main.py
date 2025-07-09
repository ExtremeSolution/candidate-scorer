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
from utils import analyze_company_profile, extract_company_pages

app = Flask(__name__)

# Load configuration from environment variables
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
REGION = os.environ.get('GCP_REGION', 'us-central1')
LOCATION = os.environ.get('GCP_LOCATION', 'us')
PROCESSOR_ID = os.environ.get('DOCUMENT_AI_PROCESSOR_ID')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-pro')
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
    """New: Extract JD from URL with security validation"""
    try:
        # Basic URL validation
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ['http', 'https']:
            return "Error: Invalid URL scheme. Only http and https are allowed."
        
        # Prevent SSRF
        hostname = parsed_url.hostname
        if not hostname or '.' not in hostname:
             return "Error: Invalid hostname."
        
        # Avoid local/internal addresses (basic check)
        if hostname == 'localhost' or hostname.startswith('127.') or hostname.startswith('10.') or hostname.startswith('192.168.'):
            return "Error: Access to local or internal addresses is not allowed."

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
    prompt = get_prompt("analyze_resume", resume_text=resume_text)
    generation_config = genai.types.GenerationConfig(temperature=0.0)
    response = model.generate_content(prompt, generation_config=generation_config)
    return response.text


def score_candidate_with_company_context(resume_data, jd_text, company_profile=None):
    """Enhanced scoring with comprehensive company context"""
    if company_profile:
        prompt = get_prompt(
            "score_candidate_with_company_context",
            resume_data=resume_data,
            jd_text=jd_text,
            company_profile=json.dumps(company_profile, indent=2)
        )
    else:
        prompt = get_prompt(
            "score_candidate",
            resume_data=resume_data,
            jd_text=jd_text
        )
    
    generation_config = genai.types.GenerationConfig(temperature=0.0)
    response = model.generate_content(prompt, generation_config=generation_config)
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
            # Clean the response to ensure it's valid JSON
            cleaned_response = re.sub(r'```json\s*|\s*```', '', resume_response).strip()
            resume_data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"Error decoding resume analysis JSON: {e}")
            print(f"Raw response was: {resume_response}")
            return jsonify({"error": "Error parsing resume analysis response"})
        except Exception as e:
            print(f"Error analyzing resume: {str(e)}")
            return jsonify({"error": f"Error analyzing resume: {str(e)}"})

        # Enhanced candidate scoring with pre-loaded company context
        try:
            scoring_response = score_candidate_with_company_context(
                json.dumps(resume_data),
                jd_text,
                COMPANY_PROFILE  # Use pre-loaded company profile
            )
            # Clean the response to ensure it's valid JSON
            cleaned_scoring_response = re.sub(r'```json\s*|\s*```', '', scoring_response).strip()
            scoring_data = json.loads(cleaned_scoring_response)
        except json.JSONDecodeError as e:
            print(f"Error decoding scoring JSON: {e}")
            print(f"Raw response was: {scoring_response}")
            return jsonify({"error": "Error parsing scoring response"})
        except Exception as e:
            print(f"Error scoring candidate: {str(e)}")
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
