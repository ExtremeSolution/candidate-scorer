#!/bin/bash

# HR Candidate Scorer - Cleanup Script
# This script removes all resources created during deployment

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

echo "🧹 Starting HR Candidate Scorer cleanup..."
echo "Project: $GCP_PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $GCP_REGION"

# Confirmation prompt
read -p "⚠️  This will DELETE all HR Scorer resources from project $GCP_PROJECT_ID. Are you sure? (y/N): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Set the project
gcloud config set project $GCP_PROJECT_ID

echo "🗑️  Deleting Cloud Run service..."
if gcloud run services describe $SERVICE_NAME --region=$GCP_REGION --quiet 2>/dev/null; then
    gcloud run services delete $SERVICE_NAME --region=$GCP_REGION --quiet
    echo "✅ Deleted Cloud Run service: $SERVICE_NAME"
else
    echo "ℹ️  Cloud Run service $SERVICE_NAME not found or already deleted"
fi

echo "🗑️  Deleting container images..."
# Delete all images with the service name tag
IMAGE_TAGS=$(gcloud container images list-tags gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME --format="value(digest)" 2>/dev/null || echo "")
if [ ! -z "$IMAGE_TAGS" ]; then
    for tag in $IMAGE_TAGS; do
        gcloud container images delete gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME@$tag --quiet 2>/dev/null || true
    done
    echo "✅ Deleted container images"
else
    echo "ℹ️  No container images found for $SERVICE_NAME"
fi

echo "🗑️  Deleting Document AI processor..."
if [ ! -z "$DOCUMENT_AI_PROCESSOR_ID" ]; then
    if gcloud alpha documentai processors describe $DOCUMENT_AI_PROCESSOR_ID --location=$GCP_LOCATION --quiet 2>/dev/null; then
        gcloud alpha documentai processors disable $DOCUMENT_AI_PROCESSOR_ID --location=$GCP_LOCATION --quiet 2>/dev/null || true
        gcloud alpha documentai processors delete $DOCUMENT_AI_PROCESSOR_ID --location=$GCP_LOCATION --quiet 2>/dev/null || true
        echo "✅ Deleted Document AI processor: $DOCUMENT_AI_PROCESSOR_ID"
    else
        echo "ℹ️  Document AI processor not found or already deleted"
    fi
else
    echo "ℹ️  No Document AI processor ID found in environment"
fi

echo "🗑️  Removing service account IAM bindings..."
# Remove IAM policy bindings for the service account
gcloud projects remove-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/documentai.apiUser" \
    --quiet 2>/dev/null || true

gcloud projects remove-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user" \
    --quiet 2>/dev/null || true

echo "🗑️  Deleting service account..."
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com --quiet 2>/dev/null; then
    gcloud iam service-accounts delete ${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com --quiet
    echo "✅ Deleted service account: ${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
else
    echo "ℹ️  Service account not found or already deleted"
fi

echo "🗑️  Cleaning up Cloud Build artifacts..."
# Delete recent builds for this project (last 10)
BUILD_IDS=$(gcloud builds list --filter="source.repoSource.repoName:$SERVICE_NAME OR images:gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME" --limit=10 --format="value(id)" 2>/dev/null || echo "")
if [ ! -z "$BUILD_IDS" ]; then
    for build_id in $BUILD_IDS; do
        gcloud builds cancel $build_id --quiet 2>/dev/null || true
    done
    echo "✅ Cancelled recent builds"
else
    echo "ℹ️  No recent builds found for $SERVICE_NAME"
fi

echo "🗑️  Cleaning up Cloud Storage artifacts..."
# Delete build artifacts from Cloud Storage
gsutil -m rm -rf gs://${GCP_PROJECT_ID}_cloudbuild/source/* 2>/dev/null || true
echo "✅ Cleaned up Cloud Storage artifacts"

# Optional: Remove user permissions (commented out by default as they might be needed for other projects)
echo ""
echo "📝 Optional: Remove user deployment permissions"
echo "   The following commands can remove the permissions granted during deployment:"
echo "   (Only run these if you don't need them for other projects)"
echo ""
USER_EMAIL=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
echo "   gcloud projects remove-iam-policy-binding $GCP_PROJECT_ID --member=\"user:$USER_EMAIL\" --role=\"roles/cloudbuild.builds.editor\""
echo "   gcloud projects remove-iam-policy-binding $GCP_PROJECT_ID --member=\"user:$USER_EMAIL\" --role=\"roles/storage.admin\""
echo "   gcloud projects remove-iam-policy-binding $GCP_PROJECT_ID --member=\"user:$USER_EMAIL\" --role=\"roles/run.admin\""

# Optional: Disable APIs
echo ""
echo "📝 Optional: Disable Google Cloud APIs"
echo "   The following commands can disable the APIs enabled during deployment:"
echo "   (Only run these if you don't need them for other services)"
echo ""
echo "   gcloud services disable documentai.googleapis.com --force"
echo "   gcloud services disable aiplatform.googleapis.com --force"
echo "   gcloud services disable generativelanguage.googleapis.com --force"
echo "   gcloud services disable run.googleapis.com --force"
echo "   gcloud services disable cloudbuild.googleapis.com --force"

# Clean up .env file
echo ""
read -p "🗑️  Remove DOCUMENT_AI_PROCESSOR_ID from .env file? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f .env ]; then
        sed -i.bak '/^DOCUMENT_AI_PROCESSOR_ID=/d' .env && rm -f .env.bak
        echo "✅ Removed DOCUMENT_AI_PROCESSOR_ID from .env file"
    fi
fi

echo ""
echo "✅ Cleanup completed successfully!"
echo ""
echo "🗑️  Resources removed:"
echo "   ✅ Cloud Run service: $SERVICE_NAME"
echo "   ✅ Container images"
echo "   ✅ Document AI processor (if existed)"
echo "   ✅ Service account: ${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
echo "   ✅ IAM policy bindings"
echo "   ✅ Cloud Build artifacts"
echo "   ✅ Cloud Storage artifacts"
echo ""
echo "💡 Note: User permissions and APIs were left enabled for other potential projects."
echo "    Use the optional commands above if you want to remove them too."
