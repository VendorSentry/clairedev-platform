
import asyncio
import json
import time
from typing import Dict, List, Set
import websockets
from dataclasses import dataclass, asdict

@dataclass
class User:
    id: str
    name: str
    avatar: str
    cursor_position: Dict = None
    active_file: str = None

@dataclass
class Operation:
    type: str  # 'insert', 'delete', 'cursor_move'
    file_path: str
    position: int
    content: str = ""
    user_id: str = ""
    timestamp: float = 0

class CollaborationManager:
    def __init__(self):
        self.workspaces: Dict[str, Dict] = {}  # workspace_id -> workspace_data
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_workspaces: Dict[str, str] = {}  # user_id -> workspace_id
    
    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        try:
            # Wait for authentication message
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            user_id = auth_data['user_id']
            workspace_id = auth_data['workspace_id']
            
            # Register connection
            self.connections[user_id] = websocket
            self.user_workspaces[user_id] = workspace_id
            
            # Initialize workspace if needed
            if workspace_id not in self.workspaces:
                self.workspaces[workspace_id] = {
                    'users': {},
                    'files': {},
                    'operations': []
                }
            
            # Add user to workspace
            self.workspaces[workspace_id]['users'][user_id] = User(
                id=user_id,
                name=auth_data.get('name', f'User {user_id[:8]}'),
                avatar=auth_data.get('avatar', '👤')
            )
            
            # Notify other users
            await self.broadcast_to_workspace(workspace_id, {
                'type': 'user_joined',
                'user': asdict(self.workspaces[workspace_id]['users'][user_id])
            }, exclude_user=user_id)
            
            # Send current state to new user
            await websocket.send(json.dumps({
                'type': 'workspace_state',
                'files': self.workspaces[workspace_id]['files'],
                'users': {uid: asdict(user) for uid, user in self.workspaces[workspace_id]['users'].items()}
            }))
            
            # Handle messages
            async for message in websocket:
                await self.handle_message(user_id, json.loads(message))
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.handle_disconnect(user_id)
    
    async def handle_message(self, user_id: str, message: Dict):
        """Handle incoming message from user"""
        workspace_id = self.user_workspaces.get(user_id)
        if not workspace_id:
            return
        
        message_type = message['type']
        
        if message_type == 'file_operation':
            await self.handle_file_operation(user_id, workspace_id, message)
        elif message_type == 'cursor_move':
            await self.handle_cursor_move(user_id, workspace_id, message)
        elif message_type == 'file_select':
            await self.handle_file_select(user_id, workspace_id, message)
    
    async def handle_file_operation(self, user_id: str, workspace_id: str, message: Dict):
        """Handle file editing operations"""
        operation = Operation(
            type=message['operation'],
            file_path=message['file_path'],
            position=message['position'],
            content=message.get('content', ''),
            user_id=user_id,
            timestamp=time.time()
        )
        
        # Apply operation to workspace
        workspace = self.workspaces[workspace_id]
        
        if operation.file_path not in workspace['files']:
            workspace['files'][operation.file_path] = ""
        
        file_content = workspace['files'][operation.file_path]
        
        if operation.type == 'insert':
            new_content = (file_content[:operation.position] + 
                          operation.content + 
                          file_content[operation.position:])
            workspace['files'][operation.file_path] = new_content
        elif operation.type == 'delete':
            end_pos = operation.position + len(operation.content)
            new_content = file_content[:operation.position] + file_content[end_pos:]
            workspace['files'][operation.file_path] = new_content
        
        # Store operation
        workspace['operations'].append(operation)
        
        # Broadcast to other users
        await self.broadcast_to_workspace(workspace_id, {
            'type': 'file_operation',
            'operation': asdict(operation)
        }, exclude_user=user_id)
    
    async def handle_cursor_move(self, user_id: str, workspace_id: str, message: Dict):
        """Handle cursor movement"""
        workspace = self.workspaces[workspace_id]
        if user_id in workspace['users']:
            workspace['users'][user_id].cursor_position = message['position']
            workspace['users'][user_id].active_file = message['file_path']
            
            await self.broadcast_to_workspace(workspace_id, {
                'type': 'cursor_update',
                'user_id': user_id,
                'position': message['position'],
                'file_path': message['file_path']
            }, exclude_user=user_id)
    
    async def handle_file_select(self, user_id: str, workspace_id: str, message: Dict):
        """Handle file selection"""
        workspace = self.workspaces[workspace_id]
        if user_id in workspace['users']:
            workspace['users'][user_id].active_file = message['file_path']
            
            await self.broadcast_to_workspace(workspace_id, {
                'type': 'file_select',
                'user_id': user_id,
                'file_path': message['file_path']
            }, exclude_user=user_id)
    
    async def broadcast_to_workspace(self, workspace_id: str, message: Dict, exclude_user: str = None):
        """Broadcast message to all users in workspace"""
        workspace = self.workspaces.get(workspace_id, {})
        users = workspace.get('users', {})
        
        for user_id in users:
            if user_id != exclude_user and user_id in self.connections:
                try:
                    await self.connections[user_id].send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    pass
    
    async def handle_disconnect(self, user_id: str):
        """Handle user disconnect"""
        workspace_id = self.user_workspaces.get(user_id)
        
        if workspace_id and workspace_id in self.workspaces:
            # Remove user from workspace
            if user_id in self.workspaces[workspace_id]['users']:
                del self.workspaces[workspace_id]['users'][user_id]
            
            # Notify other users
            await self.broadcast_to_workspace(workspace_id, {
                'type': 'user_left',
                'user_id': user_id
            })
        
        # Clean up
        if user_id in self.connections:
            del self.connections[user_id]
        if user_id in self.user_workspaces:
            del self.user_workspaces[user_id]

# WebSocket server setup
collaboration_manager = CollaborationManager()

async def start_collaboration_server():
    """Start the collaboration WebSocket server"""
    return await websockets.serve(
        collaboration_manager.handle_connection,
        "0.0.0.0",
        8765
    )
