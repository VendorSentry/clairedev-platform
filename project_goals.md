
# ClaireDev Project Goals

## Mission
Build ClaireDev - an AI-native development tool that writes clean, verifiable code directly to GitHub and validates builds via deployment platforms.

## Key Features

### Core Functionality
- **Push code to GitHub**: Automatically create repositories and upload complete project structures
- **Validate builds via Render**: Test deployed applications and parse response logs
- **Understand project scope**: Maintain context across conversations and projects
- **Support natural language input**: Process user requests in plain English

### Smart AI Assistant Capabilities
- **Project Context Awareness**: Remember previous conversations and project details
- **File Planning**: For complex requests, suggest a plan before generating code
- **Complete Code Generation**: Never use placeholders, always provide working code
- **Build Validation**: Check deployed applications and provide status feedback

### User Experience
- **Multi-tab Interface**: Chat | Files | Validate | History
- **Project Management**: Organize projects in folders with easy navigation
- **Persistent Chat**: Store conversation history per project
- **Real-time Validation**: Test deployments with one-click validation

## Technology Stack
- **AI**: GPT-4 via OpenAI API
- **Version Control**: GitHub API integration
- **Database**: SQLite for local data persistence
- **Frontend**: Single-page application with vanilla JavaScript
- **Backend**: Python Flask server
- **Deployment**: Replit hosting platform

## Development Principles
- Write complete, copy-paste ready code
- Log every step for transparency
- Ask for missing context instead of making assumptions
- Provide file-by-file implementation plans for complex projects
- Maintain conversation context across sessions
