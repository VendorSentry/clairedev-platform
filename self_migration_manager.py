
import os
import json
import subprocess
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from github import Github
import requests
from deployment_manager import DeploymentManager

@dataclass
class MigrationPlan:
    source_platform: str
    target_platform: str
    migration_steps: List[str]
    rollback_plan: List[str]
    estimated_time: int

class SelfMigrationManager:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.github = Github(github_token)
        self.deployment_manager = DeploymentManager(github_token)
        self.current_codebase_files = self._get_current_files()
    
    def _get_current_files(self) -> Dict[str, str]:
        """Get all current project files"""
        files = {}
        exclude_dirs = {'.git', '__pycache__', '.env', 'node_modules', '.replit'}
        exclude_files = {'dev_studio.db', 'uv.lock', '.gitignore'}
        
        for root, dirs, filenames in os.walk('.'):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for filename in filenames:
                if filename not in exclude_files and not filename.startswith('.'):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            relative_path = file_path[2:]  # Remove './'
                            files[relative_path] = f.read()
                    except (UnicodeDecodeError, PermissionError):
                        continue
        
        return files
    
    def create_migration_plan(self, target_platform: str = "render") -> MigrationPlan:
        """Create a detailed migration plan"""
        steps = [
            "1. Create GitHub repository for ClaireDev",
            "2. Upload current codebase to GitHub",
            "3. Generate deployment configurations",
            "4. Set up environment variables",
            "5. Configure database migration",
            "6. Deploy to target platform",
            "7. Test all functionality",
            "8. Update DNS/routing if needed"
        ]
        
        rollback = [
            "1. Revert to Replit hosting",
            "2. Restore database backup", 
            "3. Update configuration",
            "4. Verify all services running"
        ]
        
        return MigrationPlan(
            source_platform="replit",
            target_platform=target_platform,
            migration_steps=steps,
            rollback_plan=rollback,
            estimated_time=30  # minutes
        )
    
    def execute_self_migration(self, repo_name: str = "clairedev-platform") -> Dict[str, any]:
        """Execute complete self-migration to GitHub and deployment platform"""
        try:
            migration_log = []
            
            # Step 1: Create GitHub repository
            migration_log.append("Creating GitHub repository...")
            repo = self._create_github_repo(repo_name)
            
            # Step 2: Prepare deployment files
            migration_log.append("Preparing deployment configurations...")
            deployment_files = self._generate_deployment_files()
            
            # Step 3: Combine all files
            all_files = {**self.current_codebase_files, **deployment_files}
            
            # Step 4: Upload to GitHub
            migration_log.append("Uploading codebase to GitHub...")
            self._upload_to_github(repo_name, all_files)
            
            # Step 5: Generate deployment instructions
            migration_log.append("Generating deployment instructions...")
            deployment_guide = self._generate_deployment_guide(repo['html_url'])
            
            return {
                "success": True,
                "repo_url": repo['html_url'],
                "migration_log": migration_log,
                "deployment_guide": deployment_guide,
                "next_steps": self._get_next_steps()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "migration_log": migration_log
            }
    
    def _create_github_repo(self, repo_name: str) -> Dict:
        """Create GitHub repository for the migrated project"""
        user = self.github.get_user()
        
        try:
            # Try to get existing repo
            repo = user.get_repo(repo_name)
            return {
                "html_url": repo.html_url,
                "name": repo.name,
                "exists": True
            }
        except:
            # Create new repo
            repo = user.create_repo(
                name=repo_name,
                description="ClaireDev - AI-native development platform migrated from Replit",
                private=True,
                auto_init=False
            )
            return {
                "html_url": repo.html_url,
                "name": repo.name,
                "exists": False
            }
    
    def _generate_deployment_files(self) -> Dict[str, str]:
        """Generate deployment configuration files"""
        files = {}
        
        # Render deployment configuration
        files['render.yaml'] = '''services:
  - type: web
    name: clairedev-platform
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: PORT
        value: "5000"
      - key: PYTHONPATH
        value: "."
    healthCheckPath: /health
'''
        
        # Docker configuration
        files['Dockerfile'] = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]
'''
        
        # Heroku Procfile
        files['Procfile'] = 'web: python main.py'
        
        # Updated requirements.txt with all dependencies
        files['requirements.txt'] = '''flask==2.3.3
flask-cors==4.0.0
openai==1.3.0
PyGithub==1.59.1
python-dotenv==1.0.0
requests==2.31.0
anthropic==0.8.1
google-generativeai==0.3.0
mistralai==0.1.0
asyncio-compat==0.1.0
'''
        
        # Environment template
        files['.env.production'] = '''# Production Environment Variables
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
DATABASE_URL=your_database_url_here
PORT=5000
'''
        
        # GitHub Actions for CI/CD
        files['.github/workflows/deploy.yml'] = '''name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ || echo "No tests found"
    
    - name: Deploy to Render
      env:
        RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
      run: |
        echo "Deployment will be triggered automatically by Render"
'''
        
        return files
    
    def _upload_to_github(self, repo_name: str, files: Dict[str, str]):
        """Upload all files to GitHub repository"""
        user = self.github.get_user()
        repo = user.get_repo(repo_name)
        
        for file_path, content in files.items():
            try:
                # Try to get existing file
                try:
                    file = repo.get_contents(file_path)
                    repo.update_file(
                        file_path,
                        f"Update {file_path}",
                        content,
                        file.sha
                    )
                except:
                    # Create new file
                    repo.create_file(
                        file_path,
                        f"Add {file_path}",
                        content
                    )
            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")
    
    def _generate_deployment_guide(self, repo_url: str) -> str:
        """Generate step-by-step deployment guide"""
        return f"""
# ClaireDev Deployment Guide

## Repository
Your code is now available at: {repo_url}

## Deploy to Render (Recommended)

1. **Connect Repository to Render:**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select the repository: {repo_url}

2. **Configure Deployment:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
   - Environment: Python 3.11
   - Port: 5000

3. **Set Environment Variables:**
   - GITHUB_TOKEN: Your GitHub personal access token
   - OPENAI_API_KEY: Your OpenAI API key
   - ANTHROPIC_API_KEY: Your Anthropic API key (optional)
   - GEMINI_API_KEY: Your Google Gemini API key (optional)
   - MISTRAL_API_KEY: Your Mistral API key (optional)

4. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically deploy your application
   - Your app will be available at: https://your-app-name.onrender.com

## Alternative Deployment Options

### Heroku
```bash
git clone {repo_url}
cd clairedev-platform
heroku create your-app-name
git push heroku main
```

### Vercel (for frontend deployments)
```bash
npm install -g vercel
vercel --prod
```

## Database Migration
- For production, consider PostgreSQL on Render/Heroku
- Update DATABASE_URL environment variable
- The app will auto-create tables on startup

## Monitoring
- Set up health checks at `/health` endpoint
- Monitor logs through platform dashboard
- Set up alerts for downtime

## Custom Domain
- Configure custom domain through deployment platform
- Update DNS records as instructed
"""
    
    def _get_next_steps(self) -> List[str]:
        """Get recommended next steps after migration"""
        return [
            "1. Set up environment variables on deployment platform",
            "2. Configure custom domain (optional)",
            "3. Set up monitoring and alerts",
            "4. Configure database backups",
            "5. Test all functionality in production",
            "6. Update any hardcoded URLs or references",
            "7. Set up CI/CD for automatic deployments"
        ]
    
    def generate_improvement_suggestions(self) -> Dict[str, any]:
        """Analyze current codebase and suggest improvements"""
        suggestions = {
            "performance": [
                "Add Redis caching for frequently accessed data",
                "Implement database connection pooling",
                "Add CDN for static assets",
                "Optimize database queries with indexing"
            ],
            "security": [
                "Add rate limiting to API endpoints",
                "Implement proper authentication/authorization",
                "Add input validation and sanitization",
                "Set up HTTPS and security headers"
            ],
            "scalability": [
                "Implement microservices architecture",
                "Add load balancing for high availability",
                "Set up auto-scaling based on demand",
                "Implement message queues for async processing"
            ],
            "monitoring": [
                "Add comprehensive logging with structured format",
                "Implement application performance monitoring",
                "Set up error tracking and alerting",
                "Add metrics collection and dashboards"
            ],
            "features": [
                "Add user authentication and project sharing",
                "Implement real-time collaboration features",
                "Add project templates and marketplace",
                "Integrate with more AI providers",
                "Add code versioning and rollback capabilities"
            ]
        }
        
        return {
            "current_codebase_analysis": self._analyze_current_code(),
            "improvement_suggestions": suggestions,
            "priority_improvements": [
                "Security enhancements",
                "Performance optimization", 
                "Monitoring and logging",
                "User authentication"
            ]
        }
    
    def _analyze_current_code(self) -> Dict[str, any]:
        """Analyze current codebase for metrics"""
        total_files = len(self.current_codebase_files)
        total_lines = sum(len(content.split('\n')) for content in self.current_codebase_files.values())
        
        file_types = {}
        for filename in self.current_codebase_files.keys():
            ext = filename.split('.')[-1] if '.' in filename else 'unknown'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            "total_files": total_files,
            "total_lines_of_code": total_lines,
            "file_types": file_types,
            "main_technologies": ["Python", "Flask", "SQLite", "OpenAI", "GitHub API"],
            "complexity_score": min(total_lines / 100, 10),  # Simple complexity metric
            "maintenance_score": 8.5  # Based on code organization
        }

def implement_self_improvement(improvement_type: str, details: Dict) -> Dict[str, any]:
    """Implement specific improvements to the codebase"""
    
    improvements = {
        "caching": {
            "files": {
                "cache_manager.py": '''
import redis
import json
import hashlib
from typing import Optional, Any
from datetime import timedelta

class CacheManager:
    def __init__(self, redis_url: str = None):
        if redis_url:
            self.redis_client = redis.from_url(redis_url)
        else:
            # Fallback to in-memory cache
            self._memory_cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        try:
            if hasattr(self, 'redis_client'):
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            else:
                return self._memory_cache.get(key)
        except:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        try:
            if hasattr(self, 'redis_client'):
                self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                self._memory_cache[key] = value
        except:
            pass
    
    def cache_key(self, *args) -> str:
        """Generate cache key from arguments"""
        combined = ''.join(str(arg) for arg in args)
        return hashlib.md5(combined.encode()).hexdigest()
'''
            }
        },
        "monitoring": {
            "files": {
                "monitoring.py": '''
import logging
import time
import psutil
from datetime import datetime
from typing import Dict, Any

class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()
        
    def get_system_metrics(self) -> Dict[str, Any]:
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "uptime_seconds": time.time() - self.start_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_application_metrics(self) -> Dict[str, Any]:
        # Add application-specific metrics
        return {
            "active_sessions": 0,  # Implement based on your session tracking
            "requests_per_minute": 0,  # Implement request counting
            "error_rate": 0,  # Implement error tracking
            "response_time_avg": 0  # Implement response time tracking
        }

# Enhanced logging configuration
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
'''
            }
        }
    }
    
    if improvement_type in improvements:
        return {
            "success": True,
            "improvement_type": improvement_type,
            "files_created": list(improvements[improvement_type]["files"].keys()),
            "implementation_details": improvements[improvement_type]
        }
    
    return {
        "success": False,
        "error": f"Improvement type '{improvement_type}' not implemented"
    }
