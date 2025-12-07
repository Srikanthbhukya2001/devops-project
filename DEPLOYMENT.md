# Deployment Guide for Let'sTalk on AWS Elastic Beanstalk

This guide will help you deploy the Let'sTalk chat application to AWS Elastic Beanstalk using GitHub Actions.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **GitHub Repository** with your code
3. **AWS CLI** installed and configured (for initial setup)
4. **EB CLI** installed (optional, for manual deployments)

## Initial AWS Setup

### 1. Create S3 Bucket for Deployments

```bash
aws s3 mb s3://letstalk-deployments --region us-east-1
```

### 2. Create Elastic Beanstalk Application

```bash
# Option 1: Using AWS Console
# Go to Elastic Beanstalk console and create a new application named "letstalk-app"

# Option 2: Using AWS CLI
aws elasticbeanstalk create-application \
  --application-name letstalk-app \
  --description "Let'sTalk Chat Application"
```

### 3. Create Elastic Beanstalk Environment

You can create the environment via AWS Console or use EB CLI:

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB (in your project directory)
eb init -p python-3.11 letstalk-app --region us-east-1

# Create environment
eb create letstalk-prod \
  --instance-type t3.small \
  --platform "Python 3.11" \
  --region us-east-1
```

Or create via AWS Console:
- Go to Elastic Beanstalk
- Select "letstalk-app"
- Click "Create environment"
- Choose "Web server environment"
- Platform: Python 3.11
- Environment name: `letstalk-prod`
- Instance type: t3.small (or t3.micro for free tier)

## GitHub Secrets Configuration

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

1. **AWS_ACCESS_KEY_ID**: Your AWS access key ID
2. **AWS_SECRET_ACCESS_KEY**: Your AWS secret access key
3. **EB_S3_BUCKET**: Name of your S3 bucket (e.g., `letstalk-deployments`)

### Creating AWS IAM User for GitHub Actions

1. Go to AWS IAM Console
2. Create a new user: `github-actions-eb`
3. Attach policies:
   - `AWSElasticBeanstalkFullAccess`
   - `AmazonS3FullAccess` (or create custom policy with limited permissions)
4. Create access keys and add to GitHub secrets

## Environment Variables

Set these in Elastic Beanstalk Console (Configuration → Software → Environment properties):

- `SECRET_KEY`: A strong secret key for Flask sessions (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `FLASK_ENV`: `production`
- `PORT`: `8000` (usually set automatically by EB)

## Deployment Process

### Automatic Deployment (GitHub Actions)

1. Push to `main` or `master` branch
2. GitHub Actions will automatically:
   - Create a deployment package
   - Upload to S3
   - Create EB application version
   - Deploy to Elastic Beanstalk environment

### Manual Deployment

```bash
# Using EB CLI
eb deploy letstalk-prod

# Or using AWS CLI
aws elasticbeanstalk create-application-version \
  --application-name letstalk-app \
  --version-label manual-$(date +%s) \
  --source-bundle S3Bucket=letstalk-deployments,S3Key=deploy.zip

aws elasticbeanstalk update-environment \
  --application-name letstalk-app \
  --environment-name letstalk-prod \
  --version-label manual-$(date +%s)
```

## Customizing Deployment

### Update Region

Edit `.github/workflows/deploy.yml`:
```yaml
env:
  AWS_REGION: us-west-2  # Change to your preferred region
```

### Update Application/Environment Names

Edit `.github/workflows/deploy.yml`:
```yaml
env:
  EB_APPLICATION_NAME: your-app-name
  EB_ENVIRONMENT_NAME: your-env-name
```

## Database Considerations

The current setup uses SQLite (local file). For production, consider:

1. **RDS (Recommended)**: Use Amazon RDS for PostgreSQL or MySQL
2. Update `app.py` to use RDS connection string
3. Set `DATABASE_URL` environment variable in EB

Example RDS setup:
```python
# In app.py
DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{DB_PATH}')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
```

## Monitoring

- Check deployment status in GitHub Actions tab
- Monitor application health in Elastic Beanstalk console
- View logs: `eb logs` or via EB console

## Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs
2. Check EB environment events
3. Verify AWS credentials and permissions
4. Ensure S3 bucket exists and is accessible

### Application Not Starting

1. Check EB logs: `eb logs`
2. Verify Procfile is correct
3. Check environment variables
4. Ensure all dependencies are in requirements.txt

### Socket.IO Not Working

1. Ensure gunicorn with eventlet is used (already in Procfile)
2. Check security groups allow WebSocket connections
3. Verify nginx configuration allows WebSocket upgrades

## Cost Optimization

- Use t3.micro for development/testing (free tier eligible)
- Enable auto-scaling for production
- Use RDS db.t3.micro for small deployments
- Set up CloudWatch alarms for cost monitoring

## Security Best Practices

1. Use strong `SECRET_KEY` (never commit to git)
2. Enable HTTPS (EB provides free SSL certificate)
3. Configure security groups properly
4. Use IAM roles with least privilege
5. Enable database encryption if using RDS
6. Regularly update dependencies

## Next Steps

- Set up custom domain name
- Configure SSL certificate
- Set up database backups
- Configure auto-scaling
- Set up monitoring and alerts

