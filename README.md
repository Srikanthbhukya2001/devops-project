# Let'sTalk - Real-time Chat Application

A modern real-time chat application built with Flask, Socket.IO, and SQLite. Features include user profiles, posts, likes, and instant messaging with read receipts.

## Features

- 🔐 User authentication (register/login)
- 💬 Real-time messaging with Socket.IO
- ✅ Read receipts (blue double ticks)
- 👤 User profiles with bio and avatar
- 📝 Posts with like functionality
- 🔔 Browser notifications
- 📊 Unread message badges
- 🎨 Modern, responsive UI

## Tech Stack

- **Backend**: Flask, Flask-SocketIO, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite (can be upgraded to PostgreSQL/MySQL)
- **Deployment**: AWS Elastic Beanstalk

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd code
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Deployment to AWS Elastic Beanstalk

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Setup

1. **Initial AWS Setup** (one-time):
```bash
# Create S3 bucket
aws s3 mb s3://letstalk-deployments --region us-east-1

# Create EB application
aws elasticbeanstalk create-application \
  --application-name letstalk-app \
  --description "Let'sTalk Chat Application"
```

2. **Create EB Environment** via AWS Console or EB CLI

3. **Configure GitHub Secrets**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `EB_S3_BUCKET` (your S3 bucket name)

4. **Push to main branch** - GitHub Actions will automatically deploy!

## Project Structure

```
code/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # EB deployment configuration
├── .ebextensions/        # EB configuration files
├── .github/
│   └── workflows/
│       └── deploy.yml     # GitHub Actions CI/CD
├── static/
│   ├── app.js           # Client-side JavaScript
│   └── style.css        # Stylesheet
├── templates/           # Jinja2 templates
│   ├── base.html
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── chat.html
│   ├── profile.html
│   └── ...
└── DEPLOYMENT.md        # Deployment guide
```

## Environment Variables

- `SECRET_KEY`: Flask secret key (required in production)
- `FLASK_ENV`: Set to `production` for production deployment
- `PORT`: Server port (default: 5000, EB uses 8000)
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)

## Database

The application uses SQLite by default. For production, consider using:
- Amazon RDS (PostgreSQL/MySQL)
- Update `app.py` to use `DATABASE_URL` environment variable

## Security Notes

- Change `SECRET_KEY` in production
- Use strong passwords
- Enable HTTPS in production
- Consider implementing CSRF protection
- Use environment variables for sensitive data

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.

