# PowerShell setup script for Elastic Beanstalk deployment

Write-Host "Setting up Elastic Beanstalk for Let'sTalk..." -ForegroundColor Green

# Check if AWS CLI is installed
try {
    $null = Get-Command aws -ErrorAction Stop
} catch {
    Write-Host "Error: AWS CLI is not installed. Please install it first." -ForegroundColor Red
    exit 1
}

# Get region from user
$region = Read-Host "Enter AWS region (default: us-east-1)"
if ([string]::IsNullOrWhiteSpace($region)) {
    $region = "us-east-1"
}

# Get bucket name
$bucket = Read-Host "Enter S3 bucket name for deployments (default: letstalk-deployments)"
if ([string]::IsNullOrWhiteSpace($bucket)) {
    $bucket = "letstalk-deployments"
}

# Create S3 bucket
Write-Host "Creating S3 bucket: $bucket" -ForegroundColor Yellow
aws s3 mb "s3://$bucket" --region $region 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Bucket created successfully" -ForegroundColor Green
} else {
    Write-Host "Bucket may already exist" -ForegroundColor Yellow
}

# Create EB application
Write-Host "Creating Elastic Beanstalk application: letstalk-app" -ForegroundColor Yellow
aws elasticbeanstalk create-application `
    --application-name letstalk-app `
    --description "Let'sTalk Chat Application" `
    --region $region 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Application created successfully" -ForegroundColor Green
} else {
    Write-Host "Application may already exist" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Create an EB environment via AWS Console or run:"
Write-Host "   eb create letstalk-prod --platform 'Python 3.11' --region $region"
Write-Host ""
Write-Host "2. Add GitHub secrets:"
Write-Host "   - AWS_ACCESS_KEY_ID"
Write-Host "   - AWS_SECRET_ACCESS_KEY"
Write-Host "   - EB_S3_BUCKET: $bucket"
Write-Host ""
Write-Host "3. Update .github/workflows/deploy.yml with your region and bucket name"
Write-Host "4. Push to main/master branch to trigger deployment"

