#!/bin/bash
# Setup script for Elastic Beanstalk deployment

echo "Setting up Elastic Beanstalk for Let'sTalk..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Get region from user
read -p "Enter AWS region (default: us-east-1): " REGION
REGION=${REGION:-us-east-1}

# Get bucket name
read -p "Enter S3 bucket name for deployments (default: letstalk-deployments): " BUCKET
BUCKET=${BUCKET:-letstalk-deployments}

# Create S3 bucket
echo "Creating S3 bucket: $BUCKET"
aws s3 mb s3://$BUCKET --region $REGION 2>/dev/null || echo "Bucket may already exist"

# Create EB application
echo "Creating Elastic Beanstalk application: letstalk-app"
aws elasticbeanstalk create-application \
  --application-name letstalk-app \
  --description "Let'sTalk Chat Application" \
  --region $REGION 2>/dev/null || echo "Application may already exist"

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create an EB environment via AWS Console or run:"
echo "   eb create letstalk-prod --platform 'Python 3.11' --region $REGION"
echo ""
echo "2. Add GitHub secrets:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - EB_S3_BUCKET: $BUCKET"
echo ""
echo "3. Update .github/workflows/deploy.yml with your region and bucket name"
echo "4. Push to main/master branch to trigger deployment"

