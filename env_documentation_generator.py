
import os
import json
from typing import Dict, List
from github import Github
from dotenv import load_dotenv

class EnvironmentDocumentationGenerator:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.github = Github(github_token)
    
    def generate_env_documentation(self) -> Dict[str, str]:
        """Generate comprehensive environment documentation"""
        
        env_docs = {}
        
        # Main environment setup guide
        env_docs['ENVIRONMENT_SETUP.md'] = self._generate_setup_guide()
        
        # Environment variables reference
        env_docs['ENV_VARIABLES.md'] = self._generate_env_reference()
        
        # Production deployment guide
        env_docs['DEPLOYMENT_GUIDE.md'] = self._generate_deployment_guide()
        
        # Development environment guide
        env_docs['DEVELOPMENT_SETUP.md'] = self._generate_dev_setup()
        
        # Updated .env.example with detailed comments
        env_docs['.env.example'] = self._generate_detailed_env_example()
        
        return env_docs
    
    def _generate_setup_guide(self) -> str:
        return """# ClaireDev Environment Setup Guide

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/clairedev-platform.git
   cd clairedev-platform
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Environment Configuration

### Required API Keys

| Service | Key | Required | Purpose |
|---------|-----|----------|---------|
| GitHub | `GITHUB_TOKEN` | ✅ Yes | Repository creation and management |
| OpenAI | `OPENAI_API_KEY` | ✅ Yes | Primary AI code generation |
| Anthropic | `ANTHROPIC_API_KEY` | ⚠️ Optional | Claude AI integration |
| Google | `GEMINI_API_KEY` | ⚠️ Optional | Gemini AI integration |
| Mistral | `MISTRAL_API_KEY` | ⚠️ Optional | Mistral AI integration |

### Database Configuration

The application uses SQLite by default. For production deployments, set:
- `DATABASE_URL`: PostgreSQL connection string for production

## Platform-Specific Setup

### Replit (Current Platform)
- Environment variables are managed through Replit Secrets
- Database is automatically configured
- No additional setup required

### Local Development
- Create `.env` file with all required keys
- Ensure Python 3.11+ is installed
- SQLite database will be created automatically

### Production Deployment
- Use environment variables instead of `.env` file
- Configure PostgreSQL database
- Set `PORT` environment variable (default: 5000)
"""

    def _generate_env_reference(self) -> str:
        return """# Environment Variables Reference

## Core Application Variables

### `GITHUB_TOKEN`
**Required:** ✅ Yes  
**Type:** String  
**Description:** GitHub Personal Access Token with repository permissions

**How to get:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `workflow`, `write:packages`
4. Copy the token

**Example:**
```
GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890
```

### `OPENAI_API_KEY`
**Required:** ✅ Yes  
**Type:** String  
**Description:** OpenAI API key for GPT-4 code generation

**How to get:**
1. Visit https://platform.openai.com/api-keys
2. Create new secret key
3. Copy the key immediately (it won't be shown again)

**Example:**
```
OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890
```

## Optional AI Provider Keys

### `ANTHROPIC_API_KEY`
**Required:** ⚠️ Optional  
**Type:** String  
**Description:** Anthropic Claude AI integration

**How to get:**
1. Visit https://console.anthropic.com/
2. Generate API key
3. Copy the key

### `GEMINI_API_KEY`
**Required:** ⚠️ Optional  
**Type:** String  
**Description:** Google Gemini AI integration

**How to get:**
1. Visit https://makersuite.google.com/app/apikey
2. Create API key
3. Copy the key

### `MISTRAL_API_KEY`
**Required:** ⚠️ Optional  
**Type:** String  
**Description:** Mistral AI integration

**How to get:**
1. Visit https://console.mistral.ai/
2. Generate API key
3. Copy the key

## Database Configuration

### `DATABASE_URL`
**Required:** ⚠️ Production only  
**Type:** String  
**Description:** PostgreSQL connection string for production

**Format:**
```
DATABASE_URL=postgresql://username:password@host:port/database
```

**Example:**
```
DATABASE_URL=postgresql://user:pass@localhost:5432/clairedev
```

## Server Configuration

### `PORT`
**Required:** ⚠️ Optional  
**Type:** Integer  
**Description:** Port number for the web server  
**Default:** 5000

**Example:**
```
PORT=5000
```

## Security Best Practices

1. **Never commit `.env` files** - Always use `.env.example` templates
2. **Use environment-specific files** - `.env.development`, `.env.production`
3. **Rotate API keys regularly** - Especially for production environments
4. **Use secrets management** - For production deployments, use platform-specific secrets
5. **Validate environment variables** - Check required variables at startup
"""

    def _generate_deployment_guide(self) -> str:
        return """# Production Deployment Guide

## Replit Deployment (Recommended)

### 1. Prepare Environment
```bash
# Set environment variables in Replit Secrets
GITHUB_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_key
# Add other optional AI keys as needed
```

### 2. Configure Deployment
The `.replit` file is already configured for Replit deployment:
```toml
[deployment]
run = ["python3", "main.py"]
deploymentTarget = "cloudrun"
```

### 3. Deploy
1. Click the "Deploy" button in Replit
2. Choose "New deployment"
3. Configure domain settings
4. Deploy and test

## Alternative Platforms

### Render
1. Connect GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python main.py`
4. Configure environment variables
5. Deploy

### Heroku
```bash
git clone your-repo
cd clairedev-platform
heroku create your-app-name
heroku config:set GITHUB_TOKEN=your_token
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

### Vercel (Serverless)
```bash
npm install -g vercel
vercel --prod
```

## Environment Variables for Production

### Required
- `GITHUB_TOKEN`: GitHub API access
- `OPENAI_API_KEY`: Primary AI provider
- `DATABASE_URL`: PostgreSQL connection (for production)

### Optional
- `ANTHROPIC_API_KEY`: Claude AI integration
- `GEMINI_API_KEY`: Google Gemini integration
- `MISTRAL_API_KEY`: Mistral AI integration
- `PORT`: Server port (default: 5000)

## Health Checks

The application provides health check endpoints:
- `/health`: Basic health status
- `/api/status`: Detailed system status

## Database Migration

For production deployments:
1. Set up PostgreSQL database
2. Configure `DATABASE_URL`
3. Tables will be created automatically on first run

## Monitoring

### Logs
- Application logs are written to stdout
- Use platform-specific log aggregation

### Metrics
- Monitor `/health` endpoint
- Track response times and error rates
- Set up alerts for downtime

## Security Considerations

1. **HTTPS Only**: Ensure all production traffic uses HTTPS
2. **Environment Variables**: Never hardcode secrets
3. **Access Controls**: Limit GitHub token permissions
4. **Rate Limiting**: Monitor API usage limits
5. **Database Security**: Use connection pooling and SSL
"""

    def _generate_dev_setup(self) -> str:
        return """# Development Environment Setup

## Prerequisites

- Python 3.11 or higher
- Git
- GitHub account
- OpenAI account with API access

## Local Development Setup

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/clairedev-platform.git
cd clairedev-platform
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

### 3. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# For development with auto-reload
pip install watchdog
```

### 4. Database Setup
```bash
# SQLite database will be created automatically
# No additional setup required for development
```

### 5. Run Development Server
```bash
python main.py
```

The application will be available at: http://localhost:5000

## Development Workflow

### File Structure
```
clairedev-platform/
├── main.py                 # Main application entry point
├── database.py            # Database management
├── multi_ai_manager.py    # Multi-AI integration
├── workspace_manager.py   # Workspace management
├── deployment_manager.py  # Deployment utilities
├── self_migration_manager.py # Self-migration features
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

### Making Changes

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

3. **Test locally:**
   ```bash
   python main.py
   # Test your changes at http://localhost:5000
   ```

4. **Commit and push:**
   ```bash
   git add .
   git commit -m "Add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create pull request**

## Development Tools

### Code Formatting
```bash
# Install development dependencies
pip install black flake8 isort

# Format code
black .
isort .

# Check code quality
flake8 .
```

### Database Management
```bash
# View database
sqlite3 dev_studio.db
.tables
.exit
```

### Testing API Endpoints
```bash
# Test health endpoint
curl http://localhost:5000/health

# Test project creation
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a React app", "repo_name": "test-app"}'
```

## Debugging

### Common Issues

1. **Import Errors:**
   - Ensure all dependencies are installed
   - Check Python version (3.11+ required)

2. **Database Errors:**
   - Delete `dev_studio.db` to reset database
   - Check file permissions

3. **API Errors:**
   - Verify API keys in `.env`
   - Check API rate limits
   - Ensure internet connectivity

### Debug Mode
```bash
# Run with debug logging
FLASK_DEBUG=1 python main.py
```

### Environment Validation
The application automatically validates required environment variables on startup.

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Ensure all checks pass before submitting PR
"""

    def _generate_detailed_env_example(self) -> str:
        return """# ClaireDev Environment Configuration
# Copy this file to .env and fill in your actual values

# ===========================================
# REQUIRED CONFIGURATION
# ===========================================

# GitHub Personal Access Token
# Required for repository creation and management
# How to get: GitHub Settings → Developer settings → Personal access tokens
# Permissions needed: repo, workflow, write:packages
GITHUB_TOKEN=your_github_token_here

# OpenAI API Key
# Required for AI code generation using GPT-4
# How to get: https://platform.openai.com/api-keys
# Note: Requires paid OpenAI account for GPT-4 access
OPENAI_API_KEY=your_openai_api_key_here

# ===========================================
# OPTIONAL AI PROVIDERS
# ===========================================

# Anthropic Claude API Key
# Optional: Enables Claude AI integration for enhanced multi-AI collaboration
# How to get: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Gemini API Key
# Optional: Enables Google Gemini AI integration
# How to get: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Mistral AI API Key
# Optional: Enables Mistral AI integration
# How to get: https://console.mistral.ai/
MISTRAL_API_KEY=your_mistral_api_key_here

# ===========================================
# DATABASE CONFIGURATION
# ===========================================

# Database URL
# Development: Leave empty to use SQLite (automatic)
# Production: Use PostgreSQL connection string
# Format: postgresql://username:password@host:port/database
DATABASE_URL=your_database_url_here

# ===========================================
# SERVER CONFIGURATION
# ===========================================

# Server Port
# Default: 5000 (recommended for Replit compatibility)
# Change only if you have specific port requirements
PORT=5000

# ===========================================
# DEPLOYMENT SETTINGS
# ===========================================

# Environment Type
# Values: development, production, testing
ENVIRONMENT=development

# Debug Mode
# Set to 'true' for development, 'false' for production
DEBUG=true

# ===========================================
# SECURITY SETTINGS
# ===========================================

# Secret Key for Flask sessions
# Generate a random secret key for production
# You can use: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_secret_key_here

# ===========================================
# MONITORING AND LOGGING
# ===========================================

# Log Level
# Values: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# External Monitoring (Optional)
# Add your monitoring service URLs/keys here
SENTRY_DSN=your_sentry_dsn_here
NEW_RELIC_LICENSE_KEY=your_new_relic_key_here

# ===========================================
# RATE LIMITING (Optional)
# ===========================================

# API Rate Limits
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# ===========================================
# FEATURE FLAGS (Optional)
# ===========================================

# Enable/disable specific features
ENABLE_MULTI_AI=true
ENABLE_REAL_TIME_COLLABORATION=true
ENABLE_AUTO_DEPLOYMENT=true
ENABLE_SELF_MIGRATION=true

# ===========================================
# NOTES
# ===========================================

# 1. Never commit this file to version control
# 2. Keep .env.example updated when adding new variables
# 3. Use platform-specific environment variable management in production
# 4. Regularly rotate API keys for security
# 5. Test configuration changes in development first
"""
    
    def push_to_github(self, repo_name: str, docs: Dict[str, str]) -> Dict[str, any]:
        """Push environment documentation to GitHub repository"""
        try:
            user = self.github.get_user()
            repo = user.get_repo(repo_name)
            
            results = []
            
            for file_path, content in docs.items():
                try:
                    # Try to get existing file
                    try:
                        file = repo.get_contents(file_path)
                        repo.update_file(
                            file_path,
                            f"Update {file_path} - Environment documentation",
                            content,
                            file.sha
                        )
                        results.append(f"Updated: {file_path}")
                    except:
                        # Create new file
                        repo.create_file(
                            file_path,
                            f"Add {file_path} - Environment documentation",
                            content
                        )
                        results.append(f"Created: {file_path}")
                        
                except Exception as e:
                    results.append(f"Failed {file_path}: {str(e)}")
            
            return {
                "success": True,
                "repo_url": repo.html_url,
                "results": results,
                "files_processed": len(docs)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Usage function
def create_and_push_env_docs(repo_name: str = "clairedev-platform"):
    """Create and push environment documentation to GitHub"""
    load_dotenv()
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        return {"error": "GITHUB_TOKEN not found in environment variables"}
    
    generator = EnvironmentDocumentationGenerator(github_token)
    docs = generator.generate_env_documentation()
    result = generator.push_to_github(repo_name, docs)
    
    return result
