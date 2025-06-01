# ClaireDev - AI-native development tool
# Enhance the chatbot's conversational flow by adding context to AI responses.

import os
import json
import tempfile
import shutil
import time
import sys
import requests
import openai
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

# Import core dependencies
from database import DatabaseManager

# Lazy imports - only load when needed
GITHUB_AVAILABLE = False
MIGRATION_AVAILABLE = False
MULTI_AI_AVAILABLE = False

def get_github_manager():
    global github_manager, GITHUB_AVAILABLE
    if not GITHUB_AVAILABLE:
        try:
            from github import Github
            github_manager = Github(os.getenv('GITHUB_TOKEN'))
            GITHUB_AVAILABLE = True
        except ImportError:
            pass
    return github_manager if GITHUB_AVAILABLE else None

def get_multi_ai_manager():
    global multi_ai_manager, MULTI_AI_AVAILABLE
    if not MULTI_AI_AVAILABLE:
        try:
            from multi_ai_manager import MultiAIManager
            api_keys = {
                'openai': os.getenv('OPENAI_API_KEY'),
                'anthropic': os.getenv('ANTHROPIC_API_KEY')
            }
            multi_ai_manager = MultiAIManager(api_keys)
            MULTI_AI_AVAILABLE = True
        except (ImportError, Exception) as e:
            print(f"Multi-AI manager unavailable: {e}")
            MULTI_AI_AVAILABLE = False
    return multi_ai_manager if MULTI_AI_AVAILABLE else None

try:
    from quality_control import QualityControl
    QUALITY_CONTROL_AVAILABLE = True
except ImportError:
    QUALITY_CONTROL_AVAILABLE = False
    print("Quality control not available")

try:
    from deployment_manager import DeploymentManager
    DEPLOYMENT_AVAILABLE = True
except ImportError:
    DEPLOYMENT_AVAILABLE = False
    print("Deployment manager not available - advanced deployment features disabled")

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

# Initialize managers
db_manager = DatabaseManager()
db_manager.init_db()

# Initialize GitHub if token is available
github_token = os.getenv('GITHUB_TOKEN')
github_manager = None
migration_manager = None
deployment_manager = None

if github_token and GITHUB_AVAILABLE:
    try:
        github_manager = Github(github_token)
        if MIGRATION_AVAILABLE:
            migration_manager = SelfMigrationManager(github_token)
        if DEPLOYMENT_AVAILABLE:
            deployment_manager = DeploymentManager(github_token)
    except Exception as e:
        print(f"GitHub initialization failed: {e}")

# Initialize Multi-AI Manager
multi_ai_manager = None
collaborative_generator = None

if MULTI_AI_AVAILABLE:
    try:
        api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY'),
            'gemini': os.getenv('GEMINI_API_KEY'),
            'mistral': os.getenv('MISTRAL_API_KEY')
        }
        multi_ai_manager = MultiAIManager(api_keys)
        collaborative_generator = CollaborativeCodeGenerator(multi_ai_manager)
    except Exception as e:
        print(f"Multi-AI initialization failed: {e}")

# Initialize Quality Controller
quality_controller = None
if QUALITY_CONTROL_AVAILABLE:
    try:
        quality_controller = QualityControl()
    except Exception as e:
        print(f"Quality controller initialization failed: {e}")

def check_api_keys():
    """Check status of API keys"""
    status = {}

    # OpenAI Status Check
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.models.list()
        status["openai_status"] = "connected"
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        status["openai_status"] = "error"
        status["openai_error"] = str(e)

    # GitHub Status Check
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        response = requests.get('https://api.github.com/user', headers=headers)

        if response.status_code == 401:
            status["github_status"] = "warning"
            status["github_error"] = "Invalid Github token"
        elif response.status_code != 200:
            status["github_status"] = "error"
            status["github_error"] = f"Github API returned status code {response.status_code}"
        else:
            status["github_status"] = "connected"

    except requests.exceptions.RequestException as e:
        print(f"GitHub API Error: {e}")
        status["github_status"] = "error"
        status["github_error"] = str(e)

    return status

# Ensure database is properly initialized
try:
    db_manager.create_tables() # Ensure tables are created on startup
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")
    # Continue anyway - database will be created on first use

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dev Studio Chat - AI Code Generator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d1117; color: #c9d1d9; height: 100vh; display: flex; flex-direction: column; }
        .header { background: #161b22; border-bottom: 1px solid #30363d; padding: 20px; text-align: center; }
        .header h1 { color: #58a6ff; font-size: 1.8em; margin-bottom: 5px; }
        .header p { color: #8b949e; font-size: 0.9em; }
        .main-container { flex: 1; display: flex; overflow: hidden; }
        .sidebar { width: 320px; background: #161b22; border-right: 1px solid #30363d; display: flex; flex-direction: column; }
        .sidebar-header { padding: 15px; border-bottom: 1px solid #30363d; background: #0d1117; }
        .sidebar-header h3 { color: #58a6ff; font-size: 1.1em; margin-bottom: 8px; }
        .sidebar-tabs { display: flex; gap: 5px; }
        .tab-btn { padding: 6px 12px; background: transparent; border: 1px solid #30363d; color: #8b949e; border-radius: 15px; cursor: pointer; font-size: 12px; transition: all 0.2s; }
        .tab-btn.active { background: #58a6ff; color: white; border-color: #58a6ff; }
        .tab-btn:hover:not(.active) { background: rgba(88, 166, 255, 0.1); }
        .sidebar-content { flex: 1; overflow-y: auto; padding: 10px; }
        .section-item { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 8px; padding: 12px; cursor: pointer; transition: all 0.2s; }
        .section-item:hover { border-color: #58a6ff; background: rgba(88, 166, 255, 0.05); }
        .section-item.active { border-color: #58a6ff; background: rgba(88, 166, 255, 0.1); }
        .item-title { font-weight: 600; color: #c9d1d9; font-size: 14px; margin-bottom: 4px; }
        .item-meta { font-size: 11px; color: #8b949e; }
        .item-preview { font-size: 12px; color: #8b949e; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .tech-stack { display: inline-block; background: rgba(88, 166, 255, 0.2); color: #58a6ff; padding: 2px 6px; border-radius: 10px; font-size: 10px; margin-top: 4px; }
        .new-chat-btn { width: 100%; background: #238636; color: white; border: none; padding: 12px; border-radius: 8px; cursor: pointer; font-weight: 600; margin-bottom: 15px; transition: background 0.2s; }
        .new-chat-btn:hover { background: #2ea043; }
        .empty-state { text-align: center; color: #8b949e; padding: 30px 20px; font-size: 14px; }
        .sidebar-toggle { display: none; }
        .chat-container { flex: 1; display: flex; flex-direction: column; }
        .messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
        .message { max-width: 80%; padding: 15px; border-radius: 18px; word-wrap: break-word; }
        .user-message { background: #238636; color: white; align-self: flex-end; border-bottom-right-radius: 5px; }
        .assistant-message { background: #161b22; border: 1px solid #30363d; align-self: flex-start; border-bottom-left-radius: 5px; }
        .system-message { background: rgba(88, 166, 255, 0.15); border: 1px solid #58a6ff; align-self: center; text-align: center; font-size: 0.9em; }
        .input-container { padding: 20px; background: #161b22; border-top: 1px solid #30363d; }
        .input-group { display: flex; gap: 10px; align-items: center; }
        .message-input { flex: 1; padding: 12px 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 25px; color: #c9d1d9; font-size: 14px; resize: none; min-height: 45px; max-height: 120px; }
        .message-input:focus { outline: none; border-color: #58a6ff; }
        .send-btn { background: #238636; color: white; border: none; padding: 12px 20px; border-radius: 25px; cursor: pointer; font-weight: 600; transition: background 0.2s; }
        .send-btn:hover:not(:disabled) { background: #2ea043; }
        .send-btn:disabled { background: #484f58; cursor: not-allowed; }
        .typing-indicator { background: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 18px; align-self: flex-start; border-bottom-left-radius: 5px; }
        .typing-dots { display: inline-flex; gap: 4px; }
        .typing-dots span { width: 8px; height: 8px; border-radius: 50%; background: #58a6ff; animation: typing 1.4s infinite; }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-10px); } }
        .repo-link { color: #58a6ff; text-decoration: none; font-weight: 600; }
        .repo-link:hover { text-decoration: underline; }
        .file-preview { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; margin: 10px 0; padding: 10px; font-family: 'Courier New', monospace; font-size: 12px; white-space: pre-wrap; max-height: 200px; overflow-y: auto; }
        .file-name { color: #58a6ff; font-weight: 600; margin-bottom: 5px; }
        .suggestion-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .chip { background: rgba(88, 166, 255, 0.15); border: 1px solid #58a6ff; color: #58a6ff; padding: 6px 12px; border-radius: 15px; font-size: 12px; cursor: pointer; transition: all 0.2s; }
        .chip:hover { background: rgba(88, 166, 255, 0.3); }
        .api-status { margin-top: 10px; font-size: 12px; }
        .status-item { display: inline-block; margin: 0 8px; padding: 3px 8px; border-radius: 12px; font-weight: 600; }
        .status-connected { background: rgba(35, 134, 54, 0.2); color: #2ea043; border: 1px solid #2ea043; }
        .status-error { background: rgba(248, 81, 73, 0.2); color: #f85149; border: 1px solid #f85149; }
        .status-warning { background: rgba(255, 212, 59, 0.2); color: #ffd43b; border: 1px solid #ffd43b; }

        @media (max-width: 768px) {
            .sidebar { position: absolute; left: -320px; top: 0; height: 100%; z-index: 1000; transition: left 0.3s; }
            .sidebar.open { left: 0; }
            .sidebar-toggle { display: block; position: absolute; top: 15px; left: 15px; background: #58a6ff; color: white; border: none; padding: 8px; border-radius: 6px; cursor: pointer; z-index: 1001; }
            .main-container { position: relative; }
        }

        /* AI Settings Modal */
        .ai-settings-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 3000;
            justify-content: center;
            align-items: center;
        }

        .ai-settings-content {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            max-width: 500px;
            color: #c9d1d9;
        }

        .ai-settings-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .ai-settings-header h3 {
            color: #58a6ff;
            margin: 0;
        }

        .ai-setting-item {
            margin-bottom: 15px;
        }

        .ai-setting-item label {
            display: block;
            margin-bottom: 5px;
            color: #8b949e;
        }

        .ai-setting-item input[type="range"] {
            width: 100%;
        }

        .ai-setting-item select {
            width: 100%;
            background: #0d1117;
            border: 1px solid #30363d;
            color: #c9d1d9;
            padding: 8px;
            border-radius: 6px;
        }

        .ai-settings-buttons {
            text-align: right;
        }

         /* Self-Migration Options Modal */
        .migration-options-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 3000;
            justify-content: center;
            align-items: center;
        }

        .migration-options-content {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            max-width: 500px;
            color: #c9d1d9;
        }

        .migration-options-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .migration-options-header h3 {
            color: #58a6ff;
            margin: 0;
        }

        .migration-option-item {
            margin-bottom: 15px;
        }

        .migration-options-buttons {
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Dev Studio Chat</h1>
        <p>Chat with AI to generate and deploy your projects</p>
        <div id="apiStatus" class="api-status"></div>
    </div>

    <div class="main-container">
        <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>

        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h3>📁 Workspace</h3>
                <div class="sidebar-tabs">
                    <button class="tab-btn active" onclick="switchTab('chats')">💬 Chats</button>
                    <button class="tab-btn" onclick="switchTab('projects')">🚀 Projects</button>
                </div>
            </div>

            <div class="sidebar-content">
                <button class="new-chat-btn" onclick="startNewChat()">+ New Chat</button>

                <div id="chats-content">
                    <div class="empty-state">
                        Start a conversation to see your chat history here
                    </div>
                </div>

                <div id="projects-content" style="display: none;">
                    <div style="margin-bottom: 15px;">
                        <button class="new-chat-btn" onclick="createProjectFolder()" style="background: #7c3aed; margin-bottom: 8px;">+ New Folder</button>
                        <button class="new-chat-btn" onclick="showMoveProjectModal()" style="background: #059669; font-size: 12px; padding: 8px;">📁 Organize Projects</button>
                    </div>
                    <div class="empty-state">
                        Generate your first project to see it here
                    </div>
                </div>
            </div>
        </div>

        <div class="chat-container">
            <div class="messages" id="messages">
                <div class="system-message">
                    👋 Welcome! Tell me what you'd like to build and I'll help you create it step by step.
                </div>
                <div class="suggestion-chips">
                    <div class="chip" onclick="sendSuggestion('Build a todo app with React')">📝 Todo App</div>
                    <div class="chip" onclick="sendSuggestion('Create a Python API for weather data')">🌤️ Weather API</div>
                    <div class="chip" onclick="sendSuggestion('Make a portfolio website')">💼 Portfolio Site</div>
                    <div class="chip" onclick="sendSuggestion('Build a chat application')">💬 Chat App</div>
                    <div class="chip" onclick="runCapabilityTests()">🧪 Test My Capabilities</div>
                    <div class="chip" onclick="showAISettings()">⚙️ AI Settings</div>
                    <div class="chip" onclick="showMultiAIStatus()">🤖 Multi-AI Status</div>
                    <div class="chip" onclick="sendSuggestion('Build a complex enterprise application with microservices')">🏢 Enterprise App (Multi-AI)</div>
                    <div class="chip" onclick="showMigrationOptions()">🚀 Migrate to GitHub/Render</div>
                    <div class="chip" onclick="analyzeSelfImprovement()">🔧 Self-Improvement Analysis</div>
                </div>
            </div>

            <div class="input-container">
                <div class="input-group">
                    <textarea 
                        id="messageInput" 
                        class="message-input" 
                        placeholder="Describe what you want to build..."
                        rows="1"
                    ></textarea>
                    <button class="send-btn" id="sendBtn" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
    </div>

    <!-- AI Settings Modal -->
    <div class="ai-settings-modal" id="aiSettingsModal">
        <div class="ai-settings-content">
            <div class="ai-settings-header">
                <h3>⚙️ AI Settings</h3>
                <button onclick="closeAISettings()" style="background: none; border: none; color: #8b949e; font-size: 20px; cursor: pointer;">×</button>
            </div>

            <div class="ai-setting-item">
                <label for="aiModel">Model</label>
                <select id="aiModel">
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                </select>
            </div>

            <div class="ai-setting-item">
                <label for="temperature">Creativity</label>
                <input type="range" id="temperature" min="0" max="1" step="0.05" value="0.7">
            </div>

            <div class="ai-setting-item">
                <label for="maxTokens">Max Response Length</label>
                <input type="range" id="maxTokens" min="100" max="4000" step="100" value="2000">
            </div>

            <div class="ai-settings-buttons">
                <button onclick="saveAISettings()" class="send-btn">Save Settings</button>
            </div>
        </div>
    </div>

    <!-- Self-Migration Options Modal -->
    <div class="migration-options-modal" id="migrationOptionsModal">
        <div class="migration-options-content">
            <div class="migration-options-header">
                <h3>🚀 Migrate to GitHub/Render</h3>
                <button onclick="closeMigrationOptions()" style="background: none; border: none; color: #8b949e; font-size: 20px; cursor: pointer;">×</button>
            </div>

            <div class="migration-option-item">
                <p>Choose your preferred migration method:</p>
                <button onclick="migrateToGitHub()" class="send-btn">Migrate to GitHub</button>
                <button onclick="deployToRender()" class="send-btn">Deploy to Render</button>
            </div>

            <div class="migration-options-buttons">
                <button onclick="closeMigrationOptions()" class="send-btn">Cancel</button>
            </div>
        </div>
    </div>

    <script>
        let conversation = [];
        let isProcessing = false;
        let currentSessionId = generateSessionId();
        let currentActiveTab = 'chats';
        let chatSessions = [];
        let userProjects = [];

        // AI Settings - Enhanced for better conversation
        let aiSettings = {
            model: 'gpt-4',
            temperature: 0.7,
            maxTokens: 4000  // Increased for comprehensive responses
        };

        function generateSessionId() {
            return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
        }

        function sendSuggestion(text) {
            document.getElementById('messageInput').value = text;
            sendMessage();
        }

        function addMessage(content, type) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.innerHTML = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            return messageDiv;
        }

        function showTypingIndicator() {
            const indicator = addMessage(
                '<div class="typing-indicator"><div class="typing-dots"><span></span><span></span><span></span></div> AI is thinking...</div>',
                'assistant'
            );
            indicator.id = 'typing-indicator';
            return indicator;
        }

        function removeTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();
        }

        // Sidebar functionality
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('open');
        }

        function switchTab(tab) {
            currentActiveTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            document.getElementById('chats-content').style.display = tab === 'chats' ? 'block' : 'none';
            document.getElementById('projects-content').style.display = tab === 'projects' ? 'block' : 'none';

            if (tab === 'chats') {
                loadChatHistory();
            } else {
                loadUserProjects();
            }
        }

        function startNewChat() {
            currentSessionId = generateSessionId();
            conversation = [];

            // Clear messages
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = `
                <div class="system-message">
                    👋 Welcome! Tell me what you'd like to build and I'll help you create it step by step.
                </div>
                <div class="suggestion-chips">
                    <div class="chip" onclick="sendSuggestion('Build a todo app with React')">📝 Todo App</div>
                    <div class="chip" onclick="sendSuggestion('Create a Python API for weather data')">🌤️ Weather API</div>
                    <div class="chip" onclick="sendSuggestion('Make a portfolio website')">💼 Portfolio Site</div>
                    <div class="chip" onclick="sendSuggestion('Build a chat application')">💬 Chat App</div>
                    <div class="chip" onclick="runCapabilityTests()">🧪 Test My Capabilities</div>
                    <div class="chip" onclick="showAISettings()">⚙️ AI Settings</div>
                    <div class="chip" onclick="showMultiAIStatus()">🤖 Multi-AI Status</div>
                    <div class="chip" onclick="sendSuggestion('Build a complex enterprise application with microservices')">🏢 Enterprise App (Multi-AI)</div>
                    <div class="chip" onclick="showMigrationOptions()">🚀 Migrate to GitHub/Render</div>
                    <div class="chip" onclick="analyzeSelfImprovement()">🔧 Self-Improvement Analysis</div>
                </div>
            `;

            loadChatHistory();
        }

        async function loadChatHistory() {
            try {
                // Get sessions from database, not just localStorage
                const response = await fetch('/all-sessions');
                const result = await response.json();

                const chatsContent = document.getElementById('chats-content');

                if (!result.success || result.sessions.length === 0) {
                    chatsContent.innerHTML = '<div class="empty-state">Start a conversation to see your chat history here</div>';
                    return;
                }

                let html = '';
                for (const session of result.sessions.slice(0, 20)) { // Show last 20 sessions
                    const isActive = session.session_id === currentSessionId;
                    const timeAgo = getTimeAgo(session.last_active * 1000);

                    // Get the last message for preview
                    const lastMessage = session.last_message || 'New conversation';
                    const title = session.title || `Chat ${session.session_id.substring(8, 15)}`;

                    html += `
                        <div class="section-item ${isActive ? 'active' : ''}" onclick="loadChatSession('${session.session_id}', this)">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div style="flex: 1; min-width: 0; padding-right: 8px;">
                                    <div class="item-title" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${title}</div>
                                    <div class="item-meta">${timeAgo} • ${session.total_messages} messages</div>
                                </div>
                                <button onclick="deleteChatSession('${session.session_id}', event); event.stopPropagation();" style="background: #f85149; color: white; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px; cursor: pointer; flex-shrink: 0;">×</button>
                            </div>
                        </div>
                    `;
                }

                chatsContent.innerHTML = html;
            } catch (error) {
                console.error('Failed to load chat history:', error);
                document.getElementById('chats-content').innerHTML = 
                    '<div class="empty-state">Error loading chats. Check console for details.</div>';
            }
        }

        async function loadUserProjects() {
            try {
                // Load projects and folders from database
                const [projectsResponse, foldersResponse] = await Promise.all([
                    fetch('/all-projects'),
                    fetch('/project-folders')
                ]);

                const projectsResult = await projectsResponse.json();
                const foldersResult = await foldersResponse.json();

                const projectsContent = document.getElementById('projects-content');

                let html = `
                    <div style="margin-bottom: 15px;">
                        <button class="new-chat-btn" onclick="createProjectFolder()" style="background: #7c3aed; margin-bottom: 8px;">+ New Folder</button>
                        <button class="new-chat-btn" onclick="showMoveProjectModal()" style="background: #059669; font-size: 12px; padding: 8px;">📁 Organize Projects</button>
                    </div>
                `;

                if (!projectsResult.success || projectsResult.projects.length === 0) {
                    html += '<div class="empty-state">Generate your first project to see it here</div>';
                    projectsContent.innerHTML = html;
                    return;
                }

                const folders = foldersResult.success ? foldersResult.folders : [];

                // Show folders first
                for (const folder of folders) {
                    const folderProjects = projectsResult.projects.filter(p => p.folder_id === folder.id);

                    html += `
                        <div style="margin-bottom: 15px;">
                            <div style="background: #7c3aed; color: white; padding: 8px 12px; border-radius: 6px; font-weight: 600; margin-bottom: 5px; cursor: pointer;" onclick="toggleFolder('${folder.id}')">
                                📁 ${folder.name} (${folderProjects.length})
                                <span id="folder-toggle-${folder.id}" style="float: right;">▼</span>
                            </div>
                            <div id="folder-content-${folder.id}" style="margin-left: 15px;">
                    `;

                    for (const project of folderProjects) {
                        const timeAgo = getTimeAgo(project.created_at * 1000);
                        html += `
                            <div class="section-item" style="margin-bottom: 8px; cursor: pointer;">
                                <div style="display: flex; align-items: flex-start; gap: 8px;">
                                    <button onclick="deleteProject(${project.id}, event)" style="background: #f85149; color: white; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px; cursor: pointer; flex-shrink: 0;">×</button>
                                    <div style="flex: 1; min-width: 0;" onclick="viewProject('${project.id}')">
                                        <div class="item-title" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${project.repo_name}</div>
                                        <div class="item-meta">${timeAgo}</div>
                                        <div class="tech-stack">${project.tech_stack}</div>
                                        ${project.github_url ? `<div class="item-meta"><a href="${project.github_url}" target="_blank" class="repo-link" onclick="event.stopPropagation();">🔗 GitHub</a></div>` : ''}
                                    </div>
                                </div>
                            </div>
                        `;
                    }

                    html += `
                            </div>
                        </div>
                    `;
                }

                // Show unorganized projects
                const unorganizedProjects = projectsResult.projects.filter(p => !p.folder_id);
                if (unorganizedProjects.length > 0) {
                    html += `
                        <div style="margin-bottom: 15px;">
                            <div style="background: #6b7280; color: white; padding: 8px 12px; border-radius: 6px; font-weight: 600; margin-bottom: 5px;">
                                📄 Unorganized (${unorganizedProjects.length})
                            </div>
                            <div style="margin-left: 15px;">
                    `;

                    for (const project of unorganizedProjects) {
                        const timeAgo = getTimeAgo(project.created_at * 1000);
                        html += `
                            <div class="section-item" style="margin-bottom: 8px; cursor: pointer;">
                                <div style="display: flex; align-items: flex-start; gap: 8px;">
                                    <button onclick="deleteProject(${project.id}, event)" style="background: #f85149; color: white; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px; cursor: pointer; flex-shrink: 0;">×</button>
                                    <div style="flex: 1; min-width: 0;" onclick="viewProject('${project.id}')">
                                        <div class="item-title" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${project.repo_name}</div>
                                        <div class="item-meta">${timeAgo}</div>
                                        <div class="tech-stack">${project.tech_stack}</div>
                                        ${project.github_url ? `<div class="item-meta"><a href="${project.github_url}" target="_blank" class="repo-link" onclick="event.stopPropagation();">🔗 GitHub</a></div>` : ''}
                                    </div>
                                </div>
                            </div>
                        `;
                    }

                    html += `
                            </div>
                        </div>
                    `;
                }

                projectsContent.innerHTML = html;
            } catch (error) {
                console.error('Failed to load projects:', error);
                document.getElementById('projects-content').innerHTML = 
                    '<div class="empty-state">Error loading projects. Check console for details.</div>';
            }
        }

        function toggleFolder(folderId) {
            const content = document.getElementById(`folder-content-${folderId}`);
            const toggle = document.getElementById(`folder-toggle-${folderId}`);

            if (content.style.display === 'none') {
                content.style.display = 'block';
                toggle.textContent = '▼';
            } else {
                content.style.display = 'none';
                toggle.textContent = '▶';
            }
        }

        function storeChatSession(sessionId, title, lastMessage) {
            // Chat sessions are now stored in database only
            // This function is kept for compatibility but does nothing
            // Database automatically handles session storage via API calls
        }

        function deleteChatSession(sessionId, event) {
            if (event) {
                event.stopPropagation();
            }

            if (confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
                // Immediately remove the button to prevent double-clicks
                const button = event.target;
                button.disabled = true;

                                fetch(`/delete-session/${sessionId}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            loadChatHistory(); // Reload chat history
                            alert('Chat deleted successfully.');
                        } else {
                            console.error('Error deleting chat:', data.error);
                            alert('Failed to delete chat. See console for details.');
                        }
                    })
                    .catch(error => {
                        console.error('Network error:', error);
                        alert('Network error. Check console for details.');
                    })
                    .finally(() => {
                        button.disabled = false; // Re-enable the button when complete
                    });
            }
        }

        function deleteProject(projectId, event) {
            if (event) {
                event.stopPropagation();
            }

            if (confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
                // Immediately remove the button to prevent double-clicks
                const button = event.target;
                button.disabled = true;

                fetch(`/delete-project/${projectId}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            loadUserProjects(); // Reload projects
                            alert('Project deleted successfully.');
                        } else {
                            console.error('Error deleting project:', data.error);
                            alert('Failed to delete project. See console for details.');
                        }
                    })
                    .catch(error => {
                        console.error('Network error:', error);
                        alert('Network error. Check console for details.');
                    })
                    .finally(() => {
                        button.disabled = false; // Re-enable the button when complete
                    });
            }
        }

        async function loadChatSession(sessionId, element) {
            currentSessionId = sessionId;
            document.querySelectorAll('.section-item').forEach(item => item.classList.remove('active'));
            element.classList.add('active');

            try {
                const response = await fetch(`/get-session-messages/${sessionId}`);
                const result = await response.json();

                if (result.success) {
                    conversation = result.messages;
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML = '';

                    for (const message of conversation) {
                        addMessage(message.content, message.type);
                    }

                    // Add suggestion chips after loading messages
                    const suggestionChips = document.createElement('div');
                    suggestionChips.className = 'suggestion-chips';
                    suggestionChips.innerHTML = `
                        <div class="chip" onclick="sendSuggestion('Build a todo app with React')">📝 Todo App</div>
                        <div class="chip" onclick="sendSuggestion('Create a Python API for weather data')">🌤️ Weather API</div>
                        <div class="chip" onclick="sendSuggestion('Make a portfolio website')">💼 Portfolio Site</div>
                        <div class="chip" onclick="sendSuggestion('Build a chat application')">💬 Chat App</div>
                        <div class="chip" onclick="runCapabilityTests()">🧪 Test My Capabilities</div>
                        <div class="chip" onclick="showAISettings()">⚙️ AI Settings</div>
                        <div class="chip" onclick="showMultiAIStatus()">🤖 Multi-AI Status</div>
                        <div class="chip" onclick="sendSuggestion('Build a complex enterprise application with microservices')">🏢 Enterprise App (Multi-AI)</div>
                        <div class="chip" onclick="showMigrationOptions()">🚀 Migrate to GitHub/Render</div>
                        <div class="chip" onclick="analyzeSelfImprovement()">🔧 Self-Improvement Analysis</div>
                    `;

                    messagesDiv.appendChild(suggestionChips);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                } else {
                    console.error('Failed to load session:', result.error);
                    alert('Failed to load session. See console for details.');
                }
            } catch (error) {
                console.error('Failed to load session:', error);
                alert('Failed to load session. See console for details.');
            }
        }

        function viewProject(projectId) {
            // Fetch project details to display code previews
            fetch(`/get-project-details/${projectId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showProjectDetails(data.project, data.files);
                    } else {
                        alert('Error fetching project details: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Network error:', error);
                    alert('Network error. Check console for details.');
                });
        }

        function showProjectDetails(project, files) {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = `
                <h2>${project.repo_name}</h2>
                <p>${project.description}</p>
                <p>Tech Stack: ${project.tech_stack}</p>
                ${project.github_url ? `<p><a href="${project.github_url}" target="_blank" class="repo-link">GitHub Repository</a></p>` : ''}
            `;

            for (const file of files) {
                const fileDiv = document.createElement('div');
                fileDiv.className = 'file-preview';
                fileDiv.innerHTML = `
                    <div class="file-name">${file.file_path}</div>
                    <div>${file.content}</div>
                `;
                messagesDiv.appendChild(fileDiv);
            }
        }

        async function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value.trim();

            if (!message) {
                return;
            }

            messageInput.value = '';
            messageInput.style.height = 'auto';
            messageInput.rows = 1;

            addMessage(message, 'user');
            conversation.push({ content: message, type: 'user' });
            const typingIndicator = showTypingIndicator();
            isProcessing = true;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation: conversation,
                        session_id: currentSessionId,
                        ai_settings: aiSettings
                    }),
                });

                const data = await response.json();
                removeTypingIndicator();
                isProcessing = false;

                if (data.success) {
                    const assistantMessageDiv = addMessage(data.response, 'assistant');
                    conversation.push({ content: data.response, type: 'assistant' });

                    // Store chat session
                    storeChatSession(currentSessionId, data.title, data.response);

                    // Load updated history
                    loadChatHistory();
                } else {
                    addMessage('Error: ' + data.error, 'system');
                }
            } catch (error) {
                removeTypingIndicator();
                isProcessing = false;
                addMessage('Network error, please try again.', 'system');
                console.error('Error:', error);
            } finally {
                const messagesDiv = document.getElementById('messages');
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }

        function showAISettings() {
            document.getElementById('aiModel').value = aiSettings.model;
            document.getElementById('temperature').value = aiSettings.temperature;
            document.getElementById('maxTokens').value = aiSettings.maxTokens;
            document.getElementById('aiSettingsModal').style.display = 'flex';
        }

        function closeAISettings() {
            document.getElementById('aiSettingsModal').style.display = 'none';
        }

        function saveAISettings() {
            aiSettings = {
                model: document.getElementById('aiModel').value,
                temperature: parseFloat(document.getElementById('temperature').value),
                maxTokens: parseInt(document.getElementById('maxTokens').value)
            };
            closeAISettings();
            alert('AI Settings saved!');
        }

        function showMigrationOptions() {
            document.getElementById('migrationOptionsModal').style.display = 'flex';
        }

        function closeMigrationOptions() {
            document.getElementById('migrationOptionsModal').style.display = 'none';
        }

        function migrateToGitHub() {
            alert('Migrating to GitHub... (This is a placeholder)');
            closeMigrationOptions();
        }

        function deployToRender() {
            alert('Deploying to Render... (This is a placeholder)');
            closeMigrationOptions();
        }

        function getTimeAgo(timestamp) {
            const now = new Date();
            const date = new Date(timestamp);
            const diff = now - date;
            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);

            if (seconds < 60) {
                return `${seconds} seconds ago`;
            } else if (minutes < 60) {
                return `${minutes} minutes ago`;
            } else if (hours < 24) {
                return `${hours} hours ago`;
            } else if (days < 7) {
                return `${days} days ago`;
            } else {
                return date.toISOString().split('T')[0];
            }
        }

        async function createProjectFolder() {
            const folderName = prompt("Enter folder name:");
            if (folderName) {
                try {
                    const response = await fetch('/create-project-folder', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ name: folderName }),
                    });

                    const data = await response.json();
                    if (data.success) {
                        loadUserProjects();
                    } else {
                        alert('Error creating folder: ' + data.error);
                    }
                } catch (error) {
                    console.error('Network error:', error);
                    alert('Network error. Check console for details.');
                }
            }
        }

        function showMoveProjectModal() {
            alert("Move project modal - functionality pending");
        }

        function analyzeSelfImprovement() {
            alert("Analyzing AI self-improvement... (This feature is a placeholder)");
        }

        async function runCapabilityTests() {
            try {
                const response = await fetch('/run-capability-tests', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        ai_settings: aiSettings
                    }),
                });

                const data = await response.json();
                if (data.success) {
                    addMessage(data.response, 'system');
                } else {
                    addMessage('Error: ' + data.error, 'system');
                }
            } catch (error) {
                addMessage('Network error, please try again.', 'system');
                console.error('Error:', error);
            }
        }

        function showMultiAIStatus() {
            alert("Showing Multi-AI Status... (This is a placeholder)");
        }

        document.addEventListener('input', function (event) {
            if (event.target.tagName.toLowerCase() === 'textarea') {
                event.target.style.height = 'auto';
                event.target.style.height = (event.target.scrollHeight) + 'px';
                event.target.rows = 1;
            }
        }, false);

        loadChatHistory();
        loadUserProjects();

        setInterval(function() {
            fetch('/api-status')
            .then(response => response.json())
            .then(data => {
                const apiStatusDiv = document.getElementById('apiStatus');
                let statusHTML = '';

                if (data.openai_status === 'connected') {
                    statusHTML += '<span class="status-item status-connected">✅ OpenAI</span>';
                } else {
                    statusHTML += '<span class="status-item status-error">❌ OpenAI</span>';
                }

                if (data.github_status === 'connected' || data.github_status === 'warning') {
                    const statusClass = data.github_status === 'connected' ? 'status-connected' : 'status-warning';
                    const statusIcon = data.github_status === 'connected' ? '✅' : '⚠️';
                    statusHTML += `<span class="status-item ${statusClass}">${statusIcon} GitHub</span>`;
                } else {
                    statusHTML += '<span class="status-item status-error">❌ GitHub</span>';
                }

                apiStatusDiv.innerHTML = statusHTML;

            })
            .catch(error => {
                console.error('Error fetching API status:', error);
                document.getElementById('apiStatus').innerHTML = '<span class="status-item status-error">❌ API Status Error</span>';
            });
        }, 10000);
    </script>
</body>
</html>
"""

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': int(time.time()),
        'services': {
            'database': True,
            'github': github_manager is not None,
            'multi_ai': multi_ai_manager is not None,
            'quality_control': quality_controller is not None
        }
    })

@app.route('/')
def home():
    from templates import MINIMAL_TEMPLATE
    return render_template_string(MINIMAL_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data['message']
    conversation = data['conversation']
    session_id = data['session_id']
    ai_settings = data['ai_settings']

    # Import cache manager only when needed
    from cache_manager import cache
    
    # Create cache key for similar requests
    cache_key = cache.cache_key(message, len(conversation), ai_settings['model'])
    cached_response = cache.get(cache_key)
    
    if cached_response:
        print(f"Using cached response for: {message[:50]}...")
        return jsonify(cached_response)

    print(f"Session ID: {session_id}")
    print(f"Message: {message}")

    try:
        # Enhanced prompt with more context
        prompt = f"""
        You are an AI-native development tool named ClaireDev, designed to help developers build software projects.
        Your goal is to provide step-by-step guidance and code generation to assist the user in creating their project.
        Consider the full development lifecycle: planning, coding, testing, deployment.
        You can generate code, suggest file structures, provide commands, and explain concepts.
        You can assist in multiple aspects of software development, including:
        - Backend development (e.g., APIs, databases, server-side logic)
        - Frontend development (e.g., user interfaces, web applications)
        - DevOps (e.g., deployment, CI/CD pipelines)
        - Data Science (e.g. data analysis, machine learning models)

        Here are your AI settings:
        - Model: {ai_settings['model']}
        - Temperature: {ai_settings['temperature']}
        - Max Tokens: {ai_settings['maxTokens']}

        Here is the current conversation history:
        """
        for msg in conversation:
            prompt += f"{msg['type']}: {msg['content']}\n"

        prompt += f"user: {message}\n"
        prompt += "assistant:"

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.completions.create(
            model=ai_settings['model'],
            prompt=prompt,
            temperature=ai_settings['temperature'],
            max_tokens=int(ai_settings['maxTokens']),
            n=1,
            stop=None,
            frequency_penalty=0,
            presence_penalty=0,
        )

        ai_response = response.choices[0].text.strip()
        print(f"AI Response: {ai_response}")

        # Extract a title from the conversation
        title = f"Chat {session_id[8:15]}"
        if len(conversation) == 1:
            title = message[:30]

        # Store conversation in the database
        db_manager.store_message(session_id, message, 'user')
        db_manager.store_message(session_id, ai_response, 'assistant')
        db_manager.update_session_metadata(session_id, title, ai_response)

        result = {'success': True, 'response': ai_response, 'title': title}
        
        # Cache successful responses for 1 hour
        cache.set(cache_key, result, ttl=3600)
        
        return jsonify(result)

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/create-project', methods=['POST'])
def create_project():
    data = request.json
    session_id = data['session_id']
    repo_name = data['repo_name']
    description = data['description']
    tech_stack = data['tech_stack']
    code = data['code']
    folder_id = data.get('folder_id')

    try:
        # Create a project folder in a temporary directory
        temp_dir = tempfile.mkdtemp()
        repo_path = os.path.join(temp_dir, repo_name)
        os.makedirs(repo_path)

        # Initialize Git repository
        repo = git.Repo.init(repo_path)

        # Create a basic index.html file
        index_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{repo_name}</title>
        </head>
        <body>
            <h1>Welcome to {repo_name}!</h1>
            <p>{description}</p>
        </body>
        </html>
        """
        with open(os.path.join(repo_path, 'index.html'), 'w') as f:
            f.write(index_content)

        # Create a .gitignore file
        gitignore_content = """
        .DS_Store
        *.pyc
        """
        with open(os.path.join(repo_path, '.gitignore'), 'w') as f:
            f.write(gitignore_content)

        # Add and commit the files
        repo.index.add(['index.html', '.gitignore'])
        repo.index.commit("Initial commit")

        # Store project details in the database
        project_id = db_manager.create_project(
            repo_name=repo_name,
            description=description,
            tech_stack=tech_stack,
            github_url=None,
            created_at=time.time(),
            session_id=session_id,
            folder_id=folder_id
        )

        # Store file contents
        file_paths = ["index.html", ".gitignore"]
        file_contents = [index_content, gitignore_content]

        for file_path, content in zip(file_paths, file_contents):
            db_manager.store_project_file(project_id, file_path, content)

        # Create dummy files for testing
        dummy_files = [
            {"file_path": "src/App.js", "content": "console.log('Hello React!');"},
            {"file_path": "api/app.py", "content": "print('Hello Python!');"}
        ]

        for file_data in dummy_files:
            db_manager.store_project_file(project_id, file_data["file_path"], file_data["content"])

        return jsonify({
            'success': True,
            'message': f'Project "{repo_name}" created successfully.',
            'project_id': project_id
        })

    except Exception as e:
        print(f"Project creation error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get-project-details/<project_id>')
def get_project_details(project_id):
    try:
        project = db_manager.get_project(project_id)
        files = db_manager.get_project_files(project_id)

        if not project:
            return jsonify({'success': False, 'error': 'Project not found.'})

        return jsonify({
            'success': True,
            'project': project,
            'files': files
        })

    except Exception as e:
        print(f"Error fetching project details: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete-project/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    try:
        db_manager.delete_project(project_id)
        return jsonify({'success': True, 'message': 'Project deleted successfully.'})
    except Exception as e:
        print(f"Error deleting project: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/create-project-folder', methods=['POST'])
def create_project_folder():
    data = request.json
    name = data['name']

    try:
        folder_id = db_manager.create_project_folder(name)
        return jsonify({'success': True, 'folder_id': folder_id})
    except Exception as e:
        print(f"Error creating project folder: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete-session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        db_manager.delete_session(session_id)
        return jsonify({'success': True, 'message': 'Session deleted successfully.'})
    except Exception as e:
        print(f"Error deleting session: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get-session-messages/<session_id>')
def get_session_messages(session_id):
    try:
        messages = db_manager.get_session_messages(session_id)
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        print(f"Error getting session messages: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api-status')
def api_status():
    status = check_api_keys()
    return jsonify(status)

@app.route('/run-capability-tests', methods=['POST'])
def run_capability_tests():
    data = request.json
    ai_settings = data['ai_settings']

    try:
        # Create a dummy prompt to test the AI's capabilities
        test_prompt = f"""
        You are an AI-native development tool named ClaireDev. I want to test your capabilities.
        AI Settings:
        - Model: {ai_settings['model']}
        - Temperature: {ai_settings['temperature']}
        - Max Tokens: {ai_settings['maxTokens']}

        Here are some tests:
        1. Can you generate a simple HTML page with a heading and a paragraph?
        2. Can you create a Python function that adds two numbers?
        3. Can you explain the concept of microservices?

        Please provide the responses to these tests.
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.completions.create(
            model=ai_settings['model'],
            prompt=test_prompt,
            temperature=ai_settings['temperature'],
            max_tokens=int(ai_settings['maxTokens']),
            n=1,
            stop=None,
            frequency_penalty=0,
            presence_penalty=0,
        )

        ai_response = response.choices[0].text.strip()
        print(f"Capability Tests Response: {ai_response}")

        return jsonify({'success': True, 'response': ai_response})

    except Exception as e:
        print(f"Capability tests error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/all-sessions')
def get_all_sessions():
    try:
        sessions = db_manager.get_all_sessions()
        return jsonify({'success': True, 'sessions': sessions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/all-projects')
def get_all_projects():
    try:
        projects = db_manager.get_all_projects()
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/project-folders')
def get_project_folders():
    try:
        folders = db_manager.get_project_folders()
        return jsonify({'success': True, 'folders': folders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/run-quality-check', methods=['POST'])
def run_quality_check():
    try:
        if not quality_controller:
            return jsonify({
                'success': False, 
                'error': 'Quality controller not available'
            })

        data = request.json
        session_id = data['session_id']

        # Run quality check
        check_result = quality_controller.run_comprehensive_check()

        # Save result to conversation
        db_manager.save_conversation(
            session_id, 
            'assistant', 
            f"Quality Check Results:\n{json.dumps(check_result, indent=2)}"
        )

        return jsonify({
            'success': True,
            'quality_report': check_result
        })
    except Exception as e:
        print(f"Quality check error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Quality control integration before starting the Flask application.
if __name__ == '__main__':
    # Quality control check before starting
    try:
        from quality_control import pre_deployment_check
        if not pre_deployment_check():
            print("❌ Application startup blocked due to quality issues")
            sys.exit(1)
    except ImportError:
        print("⚠️  Quality control module not found - proceeding without checks")

    port = int(os.environ.get('PORT', 5000))

    # Check API status on startup
    api_status = check_api_keys()
    print("API Status:", api_status)

    app.run(host='0.0.0.0', port=port, debug=True)