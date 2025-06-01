
import os
import json
import time
import sqlite3
from typing import Dict, List, Optional
from dataclasses import dataclass
import subprocess
import threading
import queue

@dataclass
class WorkspaceTemplate:
    name: str
    description: str
    tech_stack: str
    files: Dict[str, str]
    dependencies: List[str]
    startup_commands: List[str]

class WorkspaceManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.active_workspaces = {}
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, WorkspaceTemplate]:
        """Load built-in workspace templates"""
        return {
            "full-stack-react": WorkspaceTemplate(
                name="Full-Stack React App",
                description="Complete React frontend with Node.js backend",
                tech_stack="React + Node.js + Express + MongoDB",
                files={
                    "frontend/src/App.js": self._get_react_app_template(),
                    "frontend/package.json": self._get_react_package_json(),
                    "backend/server.js": self._get_express_server_template(),
                    "backend/package.json": self._get_express_package_json(),
                    "docker-compose.yml": self._get_docker_compose_template(),
                    ".env.example": self._get_env_template(),
                    "README.md": "# Full-Stack Application\n\nGenerated with ClaireDev"
                },
                dependencies=["node", "npm", "mongodb"],
                startup_commands=[
                    "cd frontend && npm install",
                    "cd backend && npm install",
                    "docker-compose up -d mongodb",
                    "cd backend && npm run dev"
                ]
            ),
            "python-microservice": WorkspaceTemplate(
                name="Python Microservice",
                description="FastAPI microservice with PostgreSQL",
                tech_stack="Python + FastAPI + PostgreSQL",
                files={
                    "app/main.py": self._get_fastapi_main_template(),
                    "app/models.py": self._get_fastapi_models_template(),
                    "app/database.py": self._get_fastapi_db_template(),
                    "requirements.txt": self._get_python_requirements(),
                    "Dockerfile": self._get_python_dockerfile(),
                    "docker-compose.yml": self._get_python_docker_compose(),
                    ".env.example": "DATABASE_URL=postgresql://user:pass@localhost/db"
                },
                dependencies=["python3", "pip", "postgresql"],
                startup_commands=[
                    "pip install -r requirements.txt",
                    "docker-compose up -d postgres",
                    "uvicorn app.main:app --reload"
                ]
            )
        }
    
    def create_workspace_from_template(self, template_name: str, workspace_name: str, session_id: str) -> Dict:
        """Create a new workspace from template"""
        if template_name not in self.templates:
            raise ValueError(f"Template {template_name} not found")
        
        template = self.templates[template_name]
        
        # Create workspace in database
        workspace_id = self.db_manager.create_workspace(
            session_id=session_id,
            name=workspace_name,
            template_name=template_name,
            tech_stack=template.tech_stack,
            files=template.files
        )
        
        # Setup workspace environment
        workspace_path = f"/tmp/workspace_{workspace_id}"
        os.makedirs(workspace_path, exist_ok=True)
        
        # Create files
        for file_path, content in template.files.items():
            full_path = os.path.join(workspace_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        # Store workspace info
        self.active_workspaces[workspace_id] = {
            'path': workspace_path,
            'template': template,
            'session_id': session_id,
            'created_at': time.time()
        }
        
        return {
            'workspace_id': workspace_id,
            'path': workspace_path,
            'files': template.files,
            'startup_commands': template.startup_commands
        }
    
    def execute_command_in_workspace(self, workspace_id: int, command: str) -> Dict:
        """Execute command in workspace and return output"""
        if workspace_id not in self.active_workspaces:
            raise ValueError("Workspace not found")
        
        workspace_path = self.active_workspaces[workspace_id]['path']
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': True,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out after 30 seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_workspace_files(self, workspace_id: int) -> Dict[str, str]:
        """Get all files in workspace"""
        if workspace_id not in self.active_workspaces:
            raise ValueError("Workspace not found")
        
        workspace_path = self.active_workspaces[workspace_id]['path']
        files = {}
        
        for root, dirs, filenames in os.walk(workspace_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, workspace_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[relative_path] = f.read()
                except (UnicodeDecodeError, PermissionError):
                    files[relative_path] = "<binary file>"
        
        return files
    
    def update_workspace_file(self, workspace_id: int, file_path: str, content: str) -> bool:
        """Update a file in the workspace"""
        if workspace_id not in self.active_workspaces:
            raise ValueError("Workspace not found")
        
        workspace_path = self.active_workspaces[workspace_id]['path']
        full_path = os.path.join(workspace_path, file_path)
        
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    # Template methods
    def _get_react_app_template(self):
        return '''import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>ClaireDev Full-Stack App</h1>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <div>
            <p>Backend Status: {data?.status || 'Error'}</p>
            <p>Connected to: {data?.database || 'Unknown'}</p>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;'''
    
    def _get_react_package_json(self):
        return '''{
  "name": "claire-frontend",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "proxy": "http://localhost:5000"
}'''
    
    def _get_express_server_template(self):
        return '''const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/clairedev', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Routes
app.get('/api/health', (req, res) => {
  res.json({
    status: 'OK',
    database: mongoose.connection.readyState === 1 ? 'Connected' : 'Disconnected',
    timestamp: new Date().toISOString()
  });
});

app.get('/api/projects', (req, res) => {
  res.json({ projects: [] });
});

app.post('/api/projects', (req, res) => {
  const { name, description, techStack } = req.body;
  res.json({
    id: Date.now(),
    name,
    description,
    techStack,
    createdAt: new Date().toISOString()
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});'''
    
    def _get_express_package_json(self):
        return '''{
  "name": "claire-backend",
  "version": "1.0.0",
  "main": "server.js",
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "mongoose": "^7.0.3",
    "dotenv": "^16.0.3"
  },
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "devDependencies": {
    "nodemon": "^2.0.22"
  }
}'''
    
    def _get_fastapi_main_template(self):
        return '''from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app import models
import uvicorn

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ClaireDev Microservice", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "OK", "service": "ClaireDev Microservice"}

@app.get("/projects")
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    return {"projects": projects}

@app.post("/projects")
def create_project(project_data: dict, db: Session = Depends(get_db)):
    project = models.Project(**project_data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)'''
    
    def _get_fastapi_models_template(self):
        return '''from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    tech_stack = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)'''
    
    def _get_fastapi_db_template(self):
        return '''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/clairedev")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()'''
    
    def _get_python_requirements(self):
        return '''fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.7
python-dotenv==1.0.0
pydantic==2.5.0'''
    
    def _get_docker_compose_template(self):
        return '''version: '3.8'
services:
  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: clairedev
    volumes:
      - mongo_data:/data/db

  backend:
    build: ./backend
    ports:
      - "5000:5000"
    depends_on:
      - mongodb
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/clairedev

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  mongo_data:'''
    
    def _get_python_dockerfile(self):
        return '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]'''
    
    def _get_python_docker_compose(self):
        return '''version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: clairedev
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  app:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/clairedev

volumes:
  postgres_data:'''
    
    def _get_env_template(self):
        return '''# Database
MONGODB_URI=mongodb://localhost:27017/clairedev

# API Keys
OPENAI_API_KEY=your_openai_key_here
GITHUB_TOKEN=your_github_token_here

# App Settings
NODE_ENV=development
PORT=5000'''
