
# Dev Studio - AI Code Generator

A powerful development tool that generates complete project structures using OpenAI and automatically creates GitHub repositories. Your own version of a code generation platform.

## Features

- 🤖 AI-powered code generation using OpenAI GPT-4
- 📁 Automatic GitHub repository creation
- 🚀 Multiple technology stack support
- 💻 Web-based interface
- 📦 Complete project scaffolding

## Supported Tech Stacks

- React + Node.js
- Vue.js + Express
- Python Flask
- Python Django
- Next.js
- Python FastAPI

## Setup Instructions

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- `GITHUB_TOKEN`: Create a GitHub Personal Access Token with `repo` permissions
- `OPENAI_API_KEY`: Your OpenAI API key

### 2. Getting GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` scope
3. Copy the token to your `.env` file

### 3. Getting OpenAI API Key

1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key to your `.env` file

### 4. Running the Application

The application will start on port 5000 and be accessible via your Replit URL.

## Usage

1. Open the web interface
2. Enter your project details:
   - Repository name
   - Project description
   - Technology stack
3. Click "Generate Project"
4. The AI will create a complete project structure
5. A new GitHub repository will be created automatically
6. All generated files will be uploaded to GitHub

## API Endpoints

- `GET /` - Web interface
- `POST /generate` - Generate and create project
- `GET /health` - Health check

## Deployment

This application is designed to run on Replit and can be deployed easily. The generated GitHub repositories can be connected to Render or any other hosting platform for automatic deployments.

## How It Works

1. **AI Generation**: Uses OpenAI GPT-4 to generate complete project structures based on your description
2. **GitHub Integration**: Automatically creates repositories and uploads all generated files
3. **Multi-Stack Support**: Supports various technology stacks with appropriate boilerplate code
4. **Web Interface**: Provides an intuitive interface for project generation

## Security Notes

- Keep your API keys secure and never commit them to version control
- The GitHub token should have minimal required permissions
- Consider using environment-specific configurations for production

## Contributing

Feel free to extend this tool with additional technology stacks, features, or improvements!
