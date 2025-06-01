
import os
import sys
import json
from dotenv import load_dotenv
from github import Github
import requests

def migrate_to_github():
    """Migrate this project to GitHub using environment variables"""
    load_dotenv()
    
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN not found in .env file")
        return False
    
    try:
        # Initialize GitHub client
        g = Github(github_token)
        user = g.get_user()
        
        # Create repository
        repo_name = "clairedev-platform"
        print(f"🚀 Creating repository: {repo_name}")
        
        try:
            repo = user.create_repo(
                name=repo_name,
                description="ClaireDev - AI-native development platform",
                private=False,
                auto_init=False
            )
            print(f"✅ Repository created: {repo.html_url}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"📁 Repository already exists, using existing one")
                repo = user.get_repo(repo_name)
            else:
                raise e
        
        # Get all project files
        files_to_upload = {}
        exclude_files = {'.env', 'dev_studio.db', '__pycache__', '.git', 'uv.lock'}
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in exclude_files]
            for file in files:
                if file not in exclude_files and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    relative_path = file_path[2:]  # Remove './'
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            files_to_upload[relative_path] = f.read()
                    except (UnicodeDecodeError, PermissionError):
                        continue
        
        # Add deployment files
        deployment_files = {
            'requirements.txt': '''flask==2.3.3
flask-cors==4.0.0
openai==1.3.0
PyGithub==1.59.1
python-dotenv==1.0.0
requests==2.31.0
gunicorn==21.2.0''',
            
            'Procfile': 'web: gunicorn main:app --host=0.0.0.0 --port=$PORT',
            
            '.env.production': '''# Production Environment Variables
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_api_key_here
PORT=5000''',
            
            'runtime.txt': 'python-3.11.6',
            
            'app.json': json.dumps({
                "name": "ClaireDev Platform",
                "description": "AI-native development platform",
                "repository": f"https://github.com/{user.login}/{repo_name}",
                "env": {
                    "GITHUB_TOKEN": {"description": "GitHub Personal Access Token"},
                    "OPENAI_API_KEY": {"description": "OpenAI API Key"}
                }
            }, indent=2)
        }
        
        files_to_upload.update(deployment_files)
        
        # Upload files to GitHub
        print(f"📤 Uploading {len(files_to_upload)} files...")
        
        for file_path, content in files_to_upload.items():
            try:
                # Check if file exists
                try:
                    existing_file = repo.get_contents(file_path)
                    repo.update_file(
                        file_path,
                        f"Update {file_path}",
                        content,
                        existing_file.sha
                    )
                    print(f"   Updated: {file_path}")
                except:
                    # Create new file
                    repo.create_file(
                        file_path,
                        f"Add {file_path}",
                        content
                    )
                    print(f"   Created: {file_path}")
            except Exception as e:
                print(f"   ❌ Failed to upload {file_path}: {str(e)}")
        
        print(f"\n🎉 SUCCESS! Your project is now on GitHub:")
        print(f"📁 Repository: {repo.html_url}")
        print(f"\n📋 Next steps:")
        print(f"1. Visit your repository: {repo.html_url}")
        print(f"2. Set up deployment on Replit by importing this repo")
        print(f"3. Configure environment variables in your deployment")
        print(f"4. Your project will be accessible independently")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_to_github()
    if success:
        print("\n✨ Migration completed successfully!")
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)
