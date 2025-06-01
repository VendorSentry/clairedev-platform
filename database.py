import sqlite3
import json
import time

class DatabaseManager:
    def __init__(self, db_path: str = "dev_studio.db"):
        self.db_path = db_path
        self._connection = None

    def get_connection(self):
        """Get database connection with connection reuse"""
        if not hasattr(self, '_connection') or self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._connection.execute('PRAGMA journal_mode=WAL')
        return self._connection

    def init_db(self):
        """Initialize database - alias for create_tables"""
        return self.create_tables()

    def create_tables(self):
        """Create database tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL,
                last_active INTEGER NOT NULL,
                total_messages INTEGER DEFAULT 0,
                total_projects INTEGER DEFAULT 0,
                title TEXT
            )
        ''')

        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')

        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                repo_name TEXT NOT NULL,
                description TEXT,
                tech_stack TEXT,
                files TEXT,
                github_url TEXT,
                created_at INTEGER NOT NULL,
                folder_id INTEGER,
                current_phase INTEGER DEFAULT 1,
                total_phases INTEGER DEFAULT 1,
                project_plan TEXT,
                completed_features TEXT,
                next_features TEXT,
                is_ongoing BOOLEAN DEFAULT 0,
                last_updated INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                FOREIGN KEY (folder_id) REFERENCES project_folders (id)
            )
        ''')

        # Project folders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        ''')

        conn.commit()

    def get_or_create_session(self, session_id):
        """Get existing session or create new one"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session = cursor.fetchone()

        if not session:
            cursor.execute('''
                INSERT INTO sessions (session_id, created_at, last_active)
                VALUES (?, ?, ?)
            ''', (session_id, int(time.time()), int(time.time())))
            conn.commit()

        return session_id

    def save_conversation(self, session_id, role, message, metadata=None):
        """Save conversation message with enhanced context tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Extract context from message
        context_data = {
            'mentioned_files': self._extract_file_mentions(message),
            'mentioned_features': self._extract_feature_mentions(message),
            'code_intent': self._classify_intent(message)
        }

        if metadata:
            context_data.update(metadata)

        metadata_json = json.dumps(context_data)

        cursor.execute('''
            INSERT INTO conversations (session_id, role, message, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, role, message, int(time.time()), metadata_json))

        # Update session
        cursor.execute('''
            UPDATE sessions 
            SET last_active = ?, total_messages = total_messages + 1
            WHERE session_id = ?
        ''', (int(time.time()), session_id))

        conn.commit()

    def get_conversation_history(self, session_id):
        """Get conversation history for session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT role, message, timestamp, metadata
            FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (session_id,))

        history = []
        for row in cursor.fetchall():
            history.append({
                'role': row['role'],
                'message': row['message'],
                'timestamp': row['timestamp'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else None
            })

        return history

    def save_project(self, session_id, repo_name, description, tech_stack, files, github_url=None, project_plan=None, is_ongoing=False):
        """Save project to database with enhanced tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()

        files_json = json.dumps(files)
        plan_json = json.dumps(project_plan) if project_plan else None
        current_time = int(time.time())

        cursor.execute('''
            INSERT INTO projects (session_id, repo_name, description, tech_stack, files, github_url, created_at, 
                                project_plan, is_ongoing, last_updated, total_phases)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, repo_name, description, tech_stack, files_json, github_url, current_time, 
              plan_json, is_ongoing, current_time, len(project_plan.get('phases', [])) if project_plan else 1))

        project_id = cursor.lastrowid

        # Update session project count
        cursor.execute('''
            UPDATE sessions 
            SET total_projects = total_projects + 1
            WHERE session_id = ?
        ''', (session_id,))

        conn.commit()
        return project_id

    def update_project(self, project_id, files=None, current_phase=None, completed_features=None, next_features=None):
        """Update ongoing project with new files and progress"""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates = ["last_updated = ?"]
        values = [int(time.time())]

        if files:
            updates.append("files = ?")
            values.append(json.dumps(files))

        if current_phase:
            updates.append("current_phase = ?")
            values.append(current_phase)

        if completed_features:
            updates.append("completed_features = ?")
            values.append(json.dumps(completed_features))

        if next_features:
            updates.append("next_features = ?")
            values.append(json.dumps(next_features))

        values.append(project_id)

        cursor.execute(f'''
            UPDATE projects 
            SET {", ".join(updates)}
            WHERE id = ?
        ''', values)

        conn.commit()

    def get_ongoing_project(self, session_id):
        """Get the most recent ongoing project for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, repo_name, description, tech_stack, files, github_url, current_phase, 
                   total_phases, project_plan, completed_features, next_features
            FROM projects
            WHERE session_id = ? AND is_ongoing = 1
            ORDER BY last_updated DESC
            LIMIT 1
        ''', (session_id,))

        row = cursor.fetchone()
        if row:
            project = {
                'id': row['id'],
                'repo_name': row['repo_name'],
                'description': row['description'],
                'tech_stack': row['tech_stack'],
                'files': json.loads(row['files']) if row['files'] else {},
                'github_url': row['github_url'],
                'current_phase': row['current_phase'],
                'total_phases': row['total_phases'],
                'project_plan': json.loads(row['project_plan']) if row['project_plan'] else {},
                'completed_features': json.loads(row['completed_features']) if row['completed_features'] else [],
                'next_features': json.loads(row['next_features']) if row['next_features'] else []
            }
        else:
            project = None

        return project

    def mark_project_complete(self, project_id):
        """Mark a project as complete (no longer ongoing)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE projects 
            SET is_ongoing = 0, last_updated = ?
            WHERE id = ?
        ''', (int(time.time()), project_id))

        conn.commit()

    def assign_ongoing_project(self, session_id, project_id):
        """Assign a project as the ongoing project for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # First, mark all other projects in this session as not ongoing
        cursor.execute('''
            UPDATE projects 
            SET is_ongoing = 0
            WHERE session_id = ?
        ''', (session_id,))

        # Then mark the specified project as ongoing
        cursor.execute('''
            UPDATE projects 
            SET is_ongoing = 1, last_updated = ?
            WHERE id = ? AND session_id = ?
        ''', (int(time.time()), project_id, session_id))

        conn.commit()

    def get_all_projects(self):
        """Get all projects"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, session_id, repo_name, description, tech_stack, github_url, created_at, folder_id
            FROM projects
            ORDER BY created_at DESC
        ''')

        projects = []
        for row in cursor.fetchall():
            projects.append({
                'id': row['id'],
                'session_id': row['session_id'],
                'repo_name': row['repo_name'],
                'description': row['description'],
                'tech_stack': row['tech_stack'],
                'github_url': row['github_url'],
                'created_at': row['created_at'],
                'folder_id': row['folder_id']
            })

        return projects

    def get_project_by_id(self, project_id):
        """Get project by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, session_id, repo_name, description, tech_stack, files, github_url, created_at, folder_id
            FROM projects
            WHERE id = ?
        ''', (project_id,))

        row = cursor.fetchone()
        if row:
            project = {
                'id': row['id'],
                'session_id': row['session_id'],
                'repo_name': row['repo_name'],
                'description': row['description'],
                'tech_stack': row['tech_stack'],
                'files': json.loads(row['files']) if row['files'] else {},
                'github_url': row['github_url'],
                'created_at': row['created_at'],
                'folder_id': row['folder_id']
            }
        else:
            project = None

        return project

    def delete_session(self, session_id):
        """Delete session and all related data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM conversations WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM projects WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))

        conn.commit()

    def delete_project(self, project_id):
        """Delete a specific project"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))

        conn.commit()

    def get_all_sessions(self):
        """Get all sessions with metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT session_id, created_at, last_active, total_messages, total_projects, title
            FROM sessions
            ORDER BY last_active DESC
        ''')

        sessions = []
        for row in cursor.fetchall():
            # Get last message for preview
            cursor.execute('''
                SELECT message FROM conversations 
                WHERE session_id = ? AND role = 'user'
                ORDER BY timestamp DESC LIMIT 1
            ''', (row['session_id'],))

            last_msg = cursor.fetchone()
            last_message = last_msg['message'][:100] if last_msg else 'No messages'

            sessions.append({
                'session_id': row['session_id'],
                'created_at': row['created_at'],
                'last_active': row['last_active'],
                'total_messages': row['total_messages'],
                'total_projects': row['total_projects'],
                'title': row['title'] or f"Chat {row['session_id'][-8:]}",
                'last_message': last_message
            })

        return sessions

    def _extract_file_mentions(self, message):
        """Extract file names mentioned in message"""
        import re
        file_patterns = r'\b\w+\.(js|py|html|css|json|md|txt|yml|yaml)\b'
        return re.findall(file_patterns, message.lower())

    def _extract_feature_mentions(self, message):
        """Extract feature keywords from message"""
        feature_keywords = ['add', 'create', 'build', 'implement', 'fix', 'update', 'modify', 'delete', 'remove']
        return [word for word in feature_keywords if word in message.lower()]

    def _classify_intent(self, message):
        """Classify the intent of the message"""
        if any(word in message.lower() for word in ['fix', 'error', 'bug', 'broken']):
            return 'debug'
        elif any(word in message.lower() for word in ['add', 'new', 'create', 'build']):
            return 'feature'
        elif any(word in message.lower() for word in ['update', 'modify', 'change']):
            return 'modify'
        return 'general'

    def update_session_title(self, session_id, title):
        """Update session title"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE sessions SET title = ? WHERE session_id = ?
        ''', (title, session_id))

        conn.commit()

    def create_project_folder(self, folder_name):
        """Create a new project folder"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO project_folders (name, created_at)
            VALUES (?, ?)
        ''', (folder_name, int(time.time())))

        folder_id = cursor.lastrowid
        conn.commit()
        return folder_id

    def get_project_folders(self):
        """Get all project folders"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, name, created_at
            FROM project_folders
            ORDER BY name ASC
        ''')

        folders = []
        for row in cursor.fetchall():
            folders.append({
                'id': row['id'],
                'name': row['name'],
                'created_at': row['created_at']
            })

        return folders

    def assign_project_to_folder(self, project_id, folder_id):
        """Assign project to a folder"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE projects SET folder_id = ? WHERE id = ?
        ''', (folder_id, project_id))

        conn.commit()

    def get_session_stats(self, session_id):
        """Get statistics for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT total_messages, total_projects, created_at, last_active
            FROM sessions
            WHERE session_id = ?
        ''', (session_id,))

        row = cursor.fetchone()
        if row:
            stats = {
                'total_messages': row['total_messages'],
                'total_projects': row['total_projects'],
                'created_at': row['created_at'],
                'last_active': row['last_active'],
                'duration': row['last_active'] - row['created_at']
            }
        else:
            stats = None

        return stats

    def get_user_projects(self, session_id):
        """Get projects for a specific session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, repo_name, description, tech_stack, github_url, created_at
            FROM projects
            WHERE session_id = ?
            ORDER BY created_at DESC
        ''', (session_id,))

        projects = []
        for row in cursor.fetchall():
            projects.append({
                'id': row['id'],
                'repo_name': row['repo_name'],
                'description': row['description'],
                'tech_stack': row['tech_stack'],
                'github_url': row['github_url'],
                'created_at': row['created_at']
            })

        return projects

    def store_message(self, session_id, message, role):
        """Store a single message"""
        self.get_or_create_session(session_id)
        self.save_conversation(session_id, role, message)

    def update_session_metadata(self, session_id, title, last_message):
        """Update session metadata"""
        self.update_session_title(session_id, title)

    def create_project(self, **kwargs):
        """Create project with new signature"""
        return self.save_project(
            kwargs['session_id'],
            kwargs['repo_name'], 
            kwargs['description'],
            kwargs['tech_stack'],
            kwargs.get('files', {}),
            kwargs.get('github_url'),
            kwargs.get('project_plan'),
            kwargs.get('is_ongoing', False)
        )

    def store_project_file(self, project_id, file_path, content):
        """Store individual project file"""
        # Get existing project
        project = self.get_project_by_id(project_id)
        if project:
            files = project.get('files', {})
            files[file_path] = content
            # Update project with new files
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE projects SET files = ? WHERE id = ?', 
                         (json.dumps(files), project_id))
            conn.commit()

    def get_project(self, project_id):
        """Get project by ID"""
        return self.get_project_by_id(project_id)

    def get_project_files(self, project_id):
        """Get project files"""
        project = self.get_project_by_id(project_id)
        if project and project.get('files'):
            return [{'file_path': k, 'content': v} for k, v in project['files'].items()]
        return []

    def get_session_messages(self, session_id):
        """Get session messages in correct format"""
        history = self.get_conversation_history(session_id)
        return [{'content': msg['message'], 'type': msg['role']} for msg in history]