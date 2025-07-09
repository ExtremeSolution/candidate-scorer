#!/bin/bash

# HR Candidate Scorer - Automated Deployment Script
# This script sets up everything needed for a clean Google Cloud deployment

set -e  # Exit on any error

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Check required environment variables
if [ -z "$GCP_PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable is required"
    echo "Please set it in your .env file or environment"
    exit 1
fi

# Set defaults
SERVICE_NAME=${SERVICE_NAME:-hr-scorer}
GCP_REGION=${GCP_REGION:-us-central1}
GCP_LOCATION=${GCP_LOCATION:-us}
SERVICE_ACCOUNT_NAME=${SERVICE_ACCOUNT_NAME:-hr-flows-sa}
GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.5-pro}

echo "🚀 Starting HR Candidate Scorer deployment..."
echo "Project: $GCP_PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $GCP_REGION"

# Set the project
gcloud config set project $GCP_PROJECT_ID

# Check and grant necessary user permissions
echo "🔍 Checking user permissions..."
USER_EMAIL=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)

# Function to check if user has a role
check_and_grant_role() {
    local role=$1
    local role_name=$2
    
    if ! gcloud projects get-iam-policy $GCP_PROJECT_ID --flatten="bindings[].members" --format="table(bindings.role)" --filter="bindings.members:user:$USER_EMAIL AND bindings.role:$role" | grep -q "$role"; then
        echo "🔑 Granting $role_name permissions to $USER_EMAIL..."
        gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
            --member="user:$USER_EMAIL" \
            --role="$role" \
            --quiet
    fi
}

# Grant necessary permissions for deployment
check_and_grant_role "roles/cloudbuild.builds.editor" "Cloud Build Editor"
check_and_grant_role "roles/storage.admin" "Storage Admin"
check_and_grant_role "roles/run.admin" "Cloud Run Admin"

# Enable required APIs
echo "📋 Enabling required Google Cloud APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    documentai.googleapis.com \
    aiplatform.googleapis.com \
    generativelanguage.googleapis.com \
    --quiet

# Create service account if it doesn't exist
echo "🔐 Setting up service account..."
if ! gcloud iam service-accounts describe ${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com --quiet 2>/dev/null; then
    echo "Creating service account: $SERVICE_ACCOUNT_NAME"
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="HR Flows Service Account" \
        --description="Service account for HR candidate scoring application"
    
    # Wait a moment for service account to propagate
    echo "⏳ Waiting for service account to propagate..."
    sleep 10
fi

# Grant necessary permissions
echo "🔑 Granting permissions to service account..."
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/documentai.apiUser" \
    --quiet

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user" \
    --quiet

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/ml.developer" \
    --quiet

# Handle Document AI processor setup
if [ -z "$DOCUMENT_AI_PROCESSOR_ID" ]; then
    echo "📄 Setting up Document AI processor..."
    
    # First, try to list existing processors to find one with our name
    echo "🔍 Checking for existing processors..."
    EXISTING_PROCESSORS=$(curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
        "https://documentai.googleapis.com/v1/projects/$GCP_PROJECT_ID/locations/$GCP_LOCATION/processors" 2>/dev/null || echo "")
    
    if [ ! -z "$EXISTING_PROCESSORS" ]; then
        # Look for existing processor with our display name
        EXISTING_PROCESSOR_ID=$(echo "$EXISTING_PROCESSORS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    processors = data.get('processors', [])
    for processor in processors:
        if processor.get('displayName') == 'hr-scorer-processor':
            name = processor.get('name', '')
            print(name.split('/')[-1] if name else '')
            break
except:
    pass" 2>/dev/null || echo "")
        
        if [ ! -z "$EXISTING_PROCESSOR_ID" ]; then
            DOCUMENT_AI_PROCESSOR_ID="$EXISTING_PROCESSOR_ID"
            echo "✅ Found existing Document AI processor: $DOCUMENT_AI_PROCESSOR_ID"
        fi
    fi
    
    # If no existing processor found, try to create a new one
    if [ -z "$DOCUMENT_AI_PROCESSOR_ID" ]; then
        echo "🔧 Creating new Document AI processor..."
        PROCESSOR_OUTPUT=$(curl -s -X POST \
            -H "Authorization: Bearer $(gcloud auth print-access-token)" \
            -H "Content-Type: application/json" \
            -d '{
                "displayName": "hr-scorer-processor",
                "type": "FORM_PARSER_PROCESSOR"
            }' \
            "https://documentai.googleapis.com/v1/projects/$GCP_PROJECT_ID/locations/$GCP_LOCATION/processors" 2>/dev/null || echo "")
        
        if [ ! -z "$PROCESSOR_OUTPUT" ] && echo "$PROCESSOR_OUTPUT" | grep -q '"name"'; then
            # Extract processor ID from the response
            PROCESSOR_NAME=$(echo "$PROCESSOR_OUTPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('name', ''))
except:
    pass" 2>/dev/null || echo "")
            
            if [ ! -z "$PROCESSOR_NAME" ]; then
                DOCUMENT_AI_PROCESSOR_ID=$(echo "$PROCESSOR_NAME" | sed 's|.*/||')
                echo "✅ Created new Document AI processor: $DOCUMENT_AI_PROCESSOR_ID"
            fi
        else
            echo "⚠️  Could not create Document AI processor"
            if [ ! -z "$PROCESSOR_OUTPUT" ]; then
                echo "Debug: Response: $PROCESSOR_OUTPUT"
            fi
        fi
    fi
    
    # Update .env file with the processor ID if we have one
    if [ ! -z "$DOCUMENT_AI_PROCESSOR_ID" ]; then
        if [ -f .env ]; then
            # Remove existing DOCUMENT_AI_PROCESSOR_ID line if present
            sed -i.bak '/^DOCUMENT_AI_PROCESSOR_ID=/d' .env && rm -f .env.bak
            # Add the processor ID
            echo "DOCUMENT_AI_PROCESSOR_ID=$DOCUMENT_AI_PROCESSOR_ID" >> .env
            echo "✅ Updated .env file with Document AI processor ID"
        else
            echo "⚠️  Warning: .env file not found. Please add: DOCUMENT_AI_PROCESSOR_ID=$DOCUMENT_AI_PROCESSOR_ID"
        fi
    else
        echo "ℹ️  No Document AI processor available - application will use PyPDF2 fallback"
    fi
else
    echo "✅ Document AI processor ID already configured: $DOCUMENT_AI_PROCESSOR_ID"
fi

# Run company analysis (if configured)
if [ ! -z "$COMPANY_WEBSITE" ]; then
    echo "🏢 Running company analysis for enhanced scoring..."
    python3 analyze_company.py
    if [ $? -eq 0 ]; then
        echo "✅ Company analysis completed successfully"
    else
        echo "⚠️  Company analysis failed - application will use basic scoring"
        # Remove any partial company_profile.json file
        rm -f company_profile.json
    fi
else
    echo "ℹ️  No COMPANY_WEBSITE configured - using basic scoring"
fi

# Build and submit the container image
echo "🔨 Building container image..."
gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME

# Prepare environment variables for Cloud Run
ENV_VARS="GCP_PROJECT_ID=$GCP_PROJECT_ID,GCP_REGION=$GCP_REGION,GCP_LOCATION=$GCP_LOCATION,GEMINI_MODEL=$GEMINI_MODEL"
if [ ! -z "$GEMINI_API_KEY" ]; then
    ENV_VARS="$ENV_VARS,GEMINI_API_KEY=$GEMINI_API_KEY"
fi
if [ ! -z "$DOCUMENT_AI_PROCESSOR_ID" ]; then
    ENV_VARS="$ENV_VARS,DOCUMENT_AI_PROCESSOR_ID=$DOCUMENT_AI_PROCESSOR_ID"
fi
if [ ! -z "$COMPANY_WEBSITE" ]; then
    ENV_VARS="$ENV_VARS,COMPANY_WEBSITE=$COMPANY_WEBSITE"
fi

# Deploy to Cloud Run
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $GCP_REGION \
    --service-account ${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --set-env-vars="$ENV_VARS" \
    --memory=1Gi \
    --cpu=1 \
    --timeout=300 \
    --max-instances=10 \
    --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$GCP_REGION --format="value(status.url)")

echo ""
echo "✅ Deployment completed successfully!"
echo "🌐 Your HR Candidate Scorer is available at:"
echo "   $SERVICE_URL"
echo ""
echo "📝 Configuration Summary:"
echo "   Project ID: $GCP_PROJECT_ID"
echo "   Service Name: $SERVICE_NAME"
echo "   Region: $GCP_REGION"
echo "   Model: $GEMINI_MODEL"
echo "   Service Account: ${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
if [ ! -z "$DOCUMENT_AI_PROCESSOR_ID" ]; then
    echo "   Document AI Processor: $DOCUMENT_AI_PROCESSOR_ID"
else
    echo "   PDF Processing: PyPDF2 (fallback)"
fi
if [ ! -z "$COMPANY_WEBSITE" ]; then
    echo "   Enhanced Analysis: ✅ Enabled ($COMPANY_WEBSITE)"
else
    echo "   Enhanced Analysis: ⚠️ Disabled (set COMPANY_WEBSITE for enhanced scoring)"
fi
echo ""
echo "🎉 Ready to analyze candidates!"
