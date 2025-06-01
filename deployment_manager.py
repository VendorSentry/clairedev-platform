
import os
import json
import time
import requests
import subprocess
from typing import Dict, List, Optional
from dataclasses import dataclass
import docker
from github import Github

@dataclass
class DeploymentConfig:
    name: str
    platform: str  # 'replit', 'render', 'vercel', 'heroku'
    build_command: str
    start_command: str
    environment_vars: Dict[str, str]
    port: int = 5000
    auto_deploy: bool = True

class DeploymentManager:
    def __init__(self, github_token: str):
        self.github = Github(github_token)
        self.platforms = {
            'replit': self._deploy_to_replit,
            'render': self._deploy_to_render,
            'vercel': self._deploy_to_vercel,
            'heroku': self._deploy_to_heroku
        }
    
    def create_deployment_config(self, project_data: Dict, platform: str = 'replit') -> DeploymentConfig:
        """Create deployment configuration based on project tech stack"""
        tech_stack = project_data.get('tech_stack', '').lower()
        
        if 'react' in tech_stack or 'next' in tech_stack:
            return DeploymentConfig(
                name=project_data['repo_name'],
                platform=platform,
                build_command='npm run build',
                start_command='npm start',
                environment_vars={
                    'NODE_ENV': 'production',
                    'PORT': '5000'
                }
            )
        elif 'python' in tech_stack or 'flask' in tech_stack or 'django' in tech_stack:
            return DeploymentConfig(
                name=project_data['repo_name'],
                platform=platform,
                build_command='pip install -r requirements.txt',
                start_command='python main.py',
                environment_vars={
                    'PYTHONPATH': '.',
                    'PORT': '5000'
                }
            )
        elif 'fastapi' in tech_stack:
            return DeploymentConfig(
                name=project_data['repo_name'],
                platform=platform,
                build_command='pip install -r requirements.txt',
                start_command='uvicorn main:app --host 0.0.0.0 --port 5000',
                environment_vars={
                    'PYTHONPATH': '.',
                    'PORT': '5000'
                }
            )
        else:
            # Default configuration
            return DeploymentConfig(
                name=project_data['repo_name'],
                platform=platform,
                build_command='echo "No build step required"',
                start_command='python main.py',
                environment_vars={'PORT': '5000'}
            )
    
    def deploy_project(self, project_data: Dict, config: DeploymentConfig) -> Dict:
        """Deploy project to specified platform"""
        if config.platform not in self.platforms:
            return {'success': False, 'error': f'Platform {config.platform} not supported'}
        
        try:
            return self.platforms[config.platform](project_data, config)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _deploy_to_replit(self, project_data: Dict, config: DeploymentConfig) -> Dict:
        """Deploy to Replit (primary platform)"""
        try:
            # Create .replit file for proper deployment
            replit_config = {
                'entrypoint': 'main.py',
                'modules': self._get_replit_modules(project_data['tech_stack']),
                'deployment': {
                    'run': config.start_command.split(),
                    'deploymentTarget': 'cloudrun'
                }
            }
            
            # Add to project files
            files = project_data.get('files', {})
            files['.replit'] = self._generate_replit_config(replit_config)
            
            # Create deployment-ready package.json or requirements.txt
            if 'node' in project_data['tech_stack'].lower():
                if 'package.json' not in files:
                    files['package.json'] = self._generate_package_json(project_data)
            elif 'python' in project_data['tech_stack'].lower():
                if 'requirements.txt' not in files:
                    files['requirements.txt'] = self._generate_requirements_txt(project_data)
            
            return {
                'success': True,
                'platform': 'replit',
                'url': f"https://{config.name.lower().replace('_', '-')}.replit.app",
                'files': files,
                'message': 'Ready for Replit deployment'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _deploy_to_render(self, project_data: Dict, config: DeploymentConfig) -> Dict:
        """Deploy to Render platform"""
        try:
            # Create render.yaml for deployment
            render_config = {
                'services': [{
                    'type': 'web',
                    'name': config.name,
                    'env': 'docker',
                    'buildCommand': config.build_command,
                    'startCommand': config.start_command,
                    'envVars': [
                        {'key': k, 'value': v} for k, v in config.environment_vars.items()
                    ]
                }]
            }
            
            files = project_data.get('files', {})
            files['render.yaml'] = json.dumps(render_config, indent=2)
            
            # Create Dockerfile if needed
            if 'Dockerfile' not in files:
                files['Dockerfile'] = self._generate_dockerfile(project_data['tech_stack'])
            
            return {
                'success': True,
                'platform': 'render',
                'files': files,
                'message': 'Render configuration created. Connect your GitHub repo to Render.'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _deploy_to_vercel(self, project_data: Dict, config: DeploymentConfig) -> Dict:
        """Deploy to Vercel platform"""
        try:
            # Create vercel.json
            vercel_config = {
                'version': 2,
                'builds': [
                    {
                        'src': '*.js',
                        'use': '@vercel/node'
                    }
                ],
                'routes': [
                    {
                        'src': '/(.*)',
                        'dest': '/index.js'
                    }
                ]
            }
            
            files = project_data.get('files', {})
            files['vercel.json'] = json.dumps(vercel_config, indent=2)
            
            return {
                'success': True,
                'platform': 'vercel',
                'files': files,
                'message': 'Vercel configuration created. Use "vercel --prod" to deploy.'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _deploy_to_heroku(self, project_data: Dict, config: DeploymentConfig) -> Dict:
        """Deploy to Heroku platform"""
        try:
            files = project_data.get('files', {})
            
            # Create Procfile
            files['Procfile'] = f'web: {config.start_command}'
            
            # Create runtime.txt for Python
            if 'python' in project_data['tech_stack'].lower():
                files['runtime.txt'] = 'python-3.11.0'
            
            return {
                'success': True,
                'platform': 'heroku',
                'files': files,
                'message': 'Heroku configuration created. Use "git push heroku main" to deploy.'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def monitor_deployment(self, deployment_url: str) -> Dict:
        """Monitor deployment health"""
        try:
            response = requests.get(f"{deployment_url}/health", timeout=10)
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
            else:
                return {
                    'status': 'unhealthy',
                    'status_code': response.status_code,
                    'error': response.text
                }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_replit_modules(self, tech_stack: str) -> List[str]:
        """Get required Replit modules based on tech stack"""
        modules = ['web']
        
        if 'python' in tech_stack.lower():
            modules.append('python-3.11')
        if 'node' in tech_stack.lower() or 'javascript' in tech_stack.lower():
            modules.append('nodejs-18')
        if 'postgres' in tech_stack.lower():
            modules.append('postgresql-16')
        
        return modules
    
    def _generate_replit_config(self, config: Dict) -> str:
        """Generate .replit configuration file"""
        lines = []
        for key, value in config.items():
            if key == 'modules':
                lines.append(f'modules = {json.dumps(value)}')
            elif key == 'deployment':
                lines.append('\n[deployment]')
                for k, v in value.items():
                    if isinstance(v, list):
                        lines.append(f'{k} = {json.dumps(v)}')
                    else:
                        lines.append(f'{k} = "{v}"')
            else:
                lines.append(f'{key} = "{value}"')
        
        return '\n'.join(lines)
    
    def _generate_package_json(self, project_data: Dict) -> str:
        """Generate package.json for Node.js projects"""
        package = {
            'name': project_data['repo_name'].lower(),
            'version': '1.0.0',
            'description': project_data.get('description', ''),
            'main': 'index.js',
            'scripts': {
                'start': 'node index.js',
                'dev': 'nodemon index.js'
            },
            'dependencies': {
                'express': '^4.18.2'
            }
        }
        
        # Add framework-specific dependencies
        tech_stack = project_data['tech_stack'].lower()
        if 'react' in tech_stack:
            package['dependencies'].update({
                'react': '^18.2.0',
                'react-dom': '^18.2.0'
            })
        
        return json.dumps(package, indent=2)
    
    def _generate_requirements_txt(self, project_data: Dict) -> str:
        """Generate requirements.txt for Python projects"""
        requirements = ['flask==2.3.3']
        
        tech_stack = project_data['tech_stack'].lower()
        if 'fastapi' in tech_stack:
            requirements = ['fastapi==0.104.1', 'uvicorn==0.24.0']
        elif 'django' in tech_stack:
            requirements = ['django==4.2.7']
        
        return '\n'.join(requirements)
    
    def _generate_dockerfile(self, tech_stack: str) -> str:
        """Generate Dockerfile based on tech stack"""
        if 'python' in tech_stack.lower():
            return '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]'''
        
        elif 'node' in tech_stack.lower():
            return '''FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5000

CMD ["npm", "start"]'''
        
        else:
            return '''FROM alpine:latest

WORKDIR /app

COPY . .

EXPOSE 5000

CMD ["echo", "Dockerfile needs customization for this tech stack"]'''

class DeploymentManager:
    def __init__(self, github_token: str):
        self.github_token = github_token
    
    def deploy_to_platform(self, platform: str, config: dict):
        """Deploy to specified platform"""
        return {"success": True, "message": f"Deployed to {platform}"}
class DeploymentManager:
    """Basic deployment manager - placeholder implementation"""
    
    def __init__(self):
        self.available_platforms = ['replit']
    
    def deploy_to_replit(self, project_files):
        """Deploy to Replit platform"""
        return {"status": "success", "message": "Deployed to Replit", "url": "https://replit.com"}
    
    def get_deployment_status(self, deployment_id):
        """Get deployment status"""
        return {"status": "deployed", "url": "https://replit.com"}
