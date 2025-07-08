# HR Candidate Scorer

An open-source, enterprise-grade HR tool that uses Google Cloud's AI services to automatically score job candidates against job descriptions. Democratizing AI-powered candidate evaluation for organizations of all sizes.

![HR Candidate Scorer](https://img.shields.io/badge/Status-Production%20Ready-green)
![License](https://img.shields.io/badge/License-MIT-blue)
![Cloud](https://img.shields.io/badge/Cloud-Google%20Cloud-blue)

## 🎯 What it does

- **Extract job requirements** from any job posting URL
- **Analyze resumes** (PDF or text) using advanced AI
- **Score candidates** on skills match, experience, and culture fit (1-10 scale)
- **Provide interview recommendations** with focus areas and talking points
- **Generate detailed reports** with strengths, concerns, and rationale

## ✨ Key Features

- **Zero Configuration**: Automated setup with one command
- **Enhanced Culture Fit Scoring**: Comprehensive company analysis for better candidate-company fit assessment
- **Smart Fallbacks**: Uses Document AI when available, PyPDF2 as backup
- **Environment Driven**: All configuration via environment variables
- **Cost Optimized**: 85-90% cheaper than complex enterprise solutions
- **Production Ready**: Auto-scaling Cloud Run deployment
- **Open Source**: MIT licensed, fully customizable

## 🏗️ Architecture

```
[Web Interface] → [Cloud Run] → [Gemini AI]
                      ↓
               [Document AI] (PDF processing)
```

**Simple, effective, and cost-efficient.**

## 🚀 Quick Start

### Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated
- **Gemini API key** (required for AI-powered analysis)
- Basic familiarity with Google Cloud console

### 1. Get Gemini API Key

**⚠️ CRITICAL: This step is required for the application to work**

1. **Go to Google AI Studio**: https://aistudio.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click "Create API Key"**
4. **Choose "Create API key in new project"** or select existing project
5. **Copy the generated API key** (it starts with `AIza...`)

**Important**: Keep this API key secure and never commit it to version control.

### 2. Clone and Setup

```bash
git clone <your-repo-url>
cd hr-agent
cp .env.example .env
```

### 3. Configure Environment

⚠️ **SECURITY**: The `.env` file contains sensitive data and is automatically ignored by git.

Edit `.env` with your settings:

```bash
# Required
GCP_PROJECT_ID=your-project-id
GEMINI_API_KEY=AIza...your-actual-api-key-here

# Optional (will use sensible defaults)
GCP_REGION=us-central1
GEMINI_MODEL=gemini-2.5-pro
SERVICE_NAME=hr-scorer

# Enhanced Culture Fit Scoring (optional)
COMPANY_WEBSITE=https://your-company.com
```

**Security Notes**:
- ✅ `.env` file is git-ignored and won't be committed
- ✅ API keys are never included in Docker containers or Cloud Build
- ✅ Company analysis data is excluded from version control
- ⚠️ Rotate API keys regularly and monitor usage

### 4. Deploy with One Command

```bash
./deploy.sh
```

That's it! The script will:
- ✅ Enable required Google Cloud APIs
- ✅ Create service accounts and permissions
- ✅ Set up Document AI processor (if possible)
- ✅ Build and deploy to Cloud Run
- ✅ Configure all environment variables

## 🛠️ Manual Setup (Optional)

If you prefer step-by-step setup:

### Enable APIs
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    documentai.googleapis.com \
    aiplatform.googleapis.com
```

### Create Service Account
```bash
gcloud iam service-accounts create hr-flows-sa \
    --display-name="HR Flows Service Account"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:hr-flows-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/documentai.apiUser"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:hr-flows-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### Deploy Application
```bash
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/hr-scorer
gcloud run deploy hr-scorer \
    --image gcr.io/$GCP_PROJECT_ID/hr-scorer \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

## 📊 Cost Analysis

### Monthly Infrastructure Costs
| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| Cloud Run | $5-15 | Auto-scaling, pay per use |
| Document AI | $0-20 | First 1,000 pages/month free, then $1.50/1,000 pages |
| Vertex AI/Gemini | $10-30 | Text analysis and scoring |
| **Total** | **$15-65** | **vs $200-500 for enterprise solutions** |

### Cost Per 1,000 Resume Analyses
Based on real Google Cloud pricing (as of 2024):

| Component | Usage | Cost | Details |
|-----------|--------|------|---------|
| **Cloud Run** | 60,000 vCPU-seconds<br>60,000 GB-seconds<br>1,000 requests | **$1.60** | • 1 vCPU × 60s per analysis<br>• 1 GB RAM × 60s per analysis<br>• $0.40 per million requests |
| **Document AI** | 1,000 pages | **$0.00** | • First 1,000 pages/month FREE<br>• Then $1.50 per 1,000 pages<br>• Assumes 1 page per resume |
| **Gemini API** | 3.5M input tokens<br>0.5M output tokens | **$6.88** | • ~3,500 tokens per analysis<br>• $1.25 per 1M input tokens<br>• $5.00 per 1M output tokens |
| **Enhanced Analysis** | 1 company profile | **$0.00** | • Company analysis cached<br>• Shared across all candidates |
| | | | |
| **TOTAL** | **1,000 resumes** | **🎯 $8.50** | **vs $200-500/month enterprise tools** |

### Cost Comparison

| Solution Type | 1,000 Resumes | Monthly Cost | Annual Cost |
|---------------|----------------|-------------|-------------|
| **HR Candidate Scorer** | $8.50 | $15-65 | $180-780 |
| Enterprise SaaS | $200-500 | $200-500 | $2,400-6,000 |
| **Savings** | **96% cheaper** | **70-87% cheaper** | **75-92% cheaper** |

**💡 Key Insights:**
- **Pay-per-use model**: Only pay for what you analyze
- **Volume discounts**: Larger volumes become even more cost-effective  
- **No subscription fees**: Unlike enterprise solutions with fixed monthly costs
- **Transparent pricing**: All costs based on actual Google Cloud usage

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GCP_PROJECT_ID` | *required* | Your Google Cloud project ID |
| `GCP_REGION` | `us-central1` | Deployment region |
| `GCP_LOCATION` | `us` | Document AI processor location |
| `GEMINI_MODEL` | `gemini-1.5-pro` | AI model for analysis |
| `SERVICE_NAME` | `hr-scorer` | Cloud Run service name |
| `SERVICE_ACCOUNT_NAME` | `hr-flows-sa` | Service account name |
| `DOCUMENT_AI_PROCESSOR_ID` | *auto-detected/created* | Document AI processor ID |
| `COMPANY_WEBSITE` | *optional* | Company website for enhanced analysis |

### Enhanced Culture Fit Scoring

When `COMPANY_WEBSITE` is configured, the application performs comprehensive company analysis to provide multi-dimensional candidate-company fit assessment:

**Company Analysis Dimensions:**
- **Business Intelligence**: Industry sector, business model, products/services, target markets
- **Company Focus**: Core mission, strategic priorities, company values
- **Geographic Presence**: Headquarters, offices, regional operations, market focus
- **Company Culture**: Work environment, leadership style, team dynamics, communication style
- **Work Preferences**: Remote/hybrid policies, collaboration tools, work-life balance
- **Growth Stage**: Startup/scale-up/enterprise, funding status, expansion plans
- **Technical Culture**: Technologies used, innovation focus, technical approach
- **Market Position**: Competitors, market share, industry reputation

**Enhanced Scoring Metrics:**
- Skills Match (1-10)
- Experience Match (1-10)  
- Culture Fit (1-10)
- Industry Fit (1-10) *new*
- Geographic Fit (1-10) *new*
- Growth Stage Fit (1-10) *new*
- Values Alignment (1-10) *new*

**Additional Assessment Fields:**
- Company Fit Highlights
- Potential Challenges
- Onboarding Considerations
- Enhanced Interview Focus Areas

**Configuration:**
```bash
# In your .env file
COMPANY_WEBSITE=https://your-company.com
```

**Note**: `DOCUMENT_AI_PROCESSOR_ID` is automatically managed:
- If already set in `.env`, deployment skips processor setup
- If not set, script checks for existing processors with name `hr-scorer-processor`
- If existing processor found, uses its ID and updates `.env`
- If no processor exists, creates new one and updates `.env`
- If processor creation fails, app falls back to PyPDF2

### Gemini Model Options

- `gemini-1.5-pro` - Most accurate, higher cost
- `gemini-1.5-flash` - Faster, lower cost
- `gemini-2.5-pro` - Latest model (if available)

## 🎮 Usage

### For HR Teams

1. **Open the web interface** at your Cloud Run URL
2. **Paste the job posting URL** (LinkedIn, Indeed, company website, etc.)
3. **Upload candidate resume** (PDF or text file)
4. **Click "Analyze Candidate"** and wait 30-60 seconds
5. **Review the detailed scoring report**

### Sample Report

```
Candidate: John Doe
Overall Score: 8/10
Recommendation: Strong Match

Score Breakdown:
• Skills Match: 9/10
• Experience Match: 8/10  
• Culture Fit: 7/10

Strengths: React expertise, 5+ years experience, strong portfolio
Concerns: Limited backend experience, no mention of testing
Interview Focus: System design, team collaboration, testing practices
```

## 🏢 Enterprise Features

### Customization Options

- **Custom prompts**: Modify scoring criteria in `main.py`
- **Additional fields**: Extend analysis with company-specific requirements
- **Integration**: Add APIs for ATS integration
- **Branding**: Customize the web interface
- **Authentication**: Add user login and access controls

### Scaling Considerations

- **High Volume**: Increase Cloud Run memory and CPU
- **Multi-tenant**: Add user separation and data isolation  
- **Compliance**: Add audit logging and data retention policies
- **Performance**: Enable caching and batch processing

## 🛡️ Security & Privacy

- **Data Processing**: Resumes processed in memory, not stored
- **Access Control**: Configurable authentication
- **Compliance**: GDPR-friendly (no persistent storage)
- **Encryption**: All data encrypted in transit
- **Audit Trail**: Cloud Run provides request logging

## 🔍 Troubleshooting

### Common Issues

**IAM Permission Errors During Deployment**
- ✅ **FULLY AUTOMATED**: Deploy script automatically detects and grants required permissions
- ✅ **ZERO MANUAL INTERVENTION**: Handles Cloud Build Editor, Storage Admin, Cloud Run Admin roles
- ✅ **VALIDATED**: Tested end-to-end from blank GCP project to live application

**Document AI Processor Management**
- ✅ **INTELLIGENT DETECTION**: Script checks for existing processors first, reuses if found
- ✅ **AUTOMATIC CREATION**: Creates new processor only when none exists
- ✅ **ROBUST EXTRACTION**: Uses Python JSON parsing to extract processor IDs reliably
- ✅ **ENVIRONMENT SYNC**: Automatically updates .env with discovered/created processor ID
- ✅ **GRACEFUL FALLBACK**: App uses PyPDF2 when Document AI isn't available
- ✅ **SKIP LOGIC**: Skips setup entirely if processor ID already exists in .env

**Gemini API errors**  
- Verify Vertex AI API is enabled (deploy script handles this)
- Check service account permissions (deploy script handles this)
- Try different model (update `GEMINI_MODEL` in .env)

**Deployment failures**
- Ensure `GCP_PROJECT_ID` is set correctly in .env
- Verify `gcloud` authentication: `gcloud auth list`
- Check billing is enabled on project
- Run `./cleanup.sh` to clean up failed deployments

**Poor scoring accuracy**
- Adjust prompts in `main.py`
- Try different Gemini model (gemini-2.5-flash, gemini-2.5-pro)
- Ensure job descriptions are detailed and complete

**Need to Clean Up Resources**
- Run `./cleanup.sh` to remove all created resources
- Script safely removes: Cloud Run service, container images, Document AI processor, service account, IAM bindings
- Optional commands provided to remove user permissions and disable APIs

### Getting Help

1. Check the [Google Cloud Console](https://console.cloud.google.com) for service logs
2. Review Cloud Run logs for detailed error messages
3. Verify all APIs are enabled and permissions are set
4. Test with the included sample resume (`sample_resume.pdf`)

## 🤝 Contributing

We welcome contributions from the community! This project is open source and thrives on collaboration.

### How to Contribute

- 📝 **Report bugs** using our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- 💡 **Request features** using our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)  
- 🔧 **Submit code changes** following our [contributing guidelines](CONTRIBUTING.md)
- 📖 **Improve documentation** - documentation PRs are always welcome!

### Quick Start for Contributors

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with clear commit messages
4. **Add tests** for new functionality
5. **Submit a pull request** using our [PR template](.github/pull_request_template.md)

### Development Setup

```bash
# Local development
cp .env.example .env
pip install -r requirements.txt
python test_local.py  # Run tests first
python main.py        # Start local server

# Access at http://localhost:8080
```

**Read our full [Contributing Guide](CONTRIBUTING.md) for detailed guidelines and development practices.**

### Priority Contribution Areas

- 🔍 **Enhanced Scoring Algorithms**: Improve AI analysis accuracy
- 🔗 **Integrations**: LinkedIn, GitHub, ATS systems
- 🌍 **Internationalization**: Multi-language support
- 📊 **Analytics**: Advanced candidate comparison features
- 🔌 **APIs**: Webhook support and REST endpoints

## 👥 Contributors

Thanks to all the contributors who help make this project better!

<!-- Contributors will be automatically updated -->
<a href="https://github.com/extremesolution/hr-agent/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=extremesolution/hr-agent" />
</a>

*Want to see your avatar here? [Start contributing!](CONTRIBUTING.md)*

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- [ ] **Batch Processing**: Upload multiple resumes at once
- [ ] **ATS Integration**: Connect with popular HR systems  
- [ ] **Advanced Analytics**: Historical scoring trends
- [ ] **Custom Models**: Fine-tune scoring for specific roles
- [ ] **Mobile App**: iOS/Android companion app
- [ ] **API Endpoints**: REST API for programmatic access

## 💡 Why This Solution?

**Built for Real HR Teams**
- Fast screening (30-60 seconds per candidate)
- Consistent scoring across all reviewers
- Detailed interview guidance
- Cost-effective scaling

**Technologically Sound**
- Leverages Google's latest AI models
- Proven cloud infrastructure
- Smart fallback mechanisms
- Production-ready security

**Open Source Advantages**
- Full customization control
- No vendor lock-in
- Community-driven improvements
- Transparent AI scoring

---

**Ready to revolutionize your hiring process?**

Deploy now with `./deploy.sh` and start scoring candidates in minutes!

⭐ Star this repo if you find it useful!
