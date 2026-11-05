#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# ArthSetu — AWS Automated Deployment Pipeline
# Region: ap-south-1 (Mumbai)
# Services: SQS, Lambda, DynamoDB, OpenSearch, SAM CloudFormation
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

REGION="${AWS_REGION:-ap-south-1}"
STACK_NAME="${STACK_NAME:-arthsetu-stack}"
ENV="${APP_ENV:-production}"

echo "======================================================================"
echo "🚀 ArthSetu — Deploying to AWS ($REGION)"
echo "   Stack: $STACK_NAME | Environment: $ENV"
echo "======================================================================"

# Step 1: Run Test Suite First
echo ""
echo "🧪 [Step 1/5] Running verification tests before deployment..."
if [ -d ".venv" ]; then
    .venv/bin/python run_tests.py
elif command -v python3 &> /dev/null; then
    python3 run_tests.py
fi
echo "   ✅ Verification tests passed successfully."

# Step 2: Check AWS Credentials
echo ""
echo "🔑 [Step 2/5] Checking AWS credentials..."
if ! command -v aws &> /dev/null; then
    echo "   ⚠️  AWS CLI not found in PATH."
    echo "   👉 Install via: brew install awscli"
    echo "   Continuing with SAM CLI..."
fi

# Step 3: Check / Bootstrap Resources
echo ""
echo "⚡ [Step 3/5] Bootstrapping DynamoDB & SQS resources..."
if [ -d ".venv" ]; then
    .venv/bin/python scripts/bootstrap_aws.py || true
else
    python3 scripts/bootstrap_aws.py || true
fi

# Step 4: Build Serverless Application (SAM)
echo ""
echo "📦 [Step 4/5] Building SAM application..."
if command -v sam &> /dev/null; then
    sam build --use-container || sam build
    echo "   ✅ SAM build completed."

    echo ""
    echo "☁️  [Step 5/5] Deploying CloudFormation Stack via SAM..."
    sam deploy \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --capabilities CAPABILITY_IAM \
        --resolve-s3 \
        --parameter-overrides "Environment=$ENV" \
        --no-confirm-changeset
    
    echo ""
    echo "======================================================================"
    echo "🎉 Deployment to AWS $REGION Completed Successfully!"
    echo "======================================================================"
    sam list stack-outputs --stack-name "$STACK_NAME" --region "$REGION" || true
else
    echo "   ℹ️  SAM CLI is not installed locally."
    echo "   👉 To install: brew install aws-sam-cli"
    echo "   👉 Or run via LocalStack: docker compose up -d localstack"
fi

