
# Lightweight HTML template (reduced size)
MINIMAL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClaireDev - Lightweight</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; background: #1a1a1a; color: #fff; height: 100vh; display: flex; flex-direction: column; }
        .header { background: #2a2a2a; padding: 15px; text-align: center; border-bottom: 1px solid #333; }
        .chat-container { flex: 1; display: flex; flex-direction: column; max-width: 800px; margin: 0 auto; width: 100%; }
        .messages { flex: 1; padding: 20px; overflow-y: auto; }
        .message { margin: 10px 0; padding: 12px; border-radius: 8px; max-width: 80%; }
        .user-message { background: #0066cc; margin-left: auto; }
        .assistant-message { background: #333; }
        .input-container { padding: 20px; background: #2a2a2a; }
        .input-group { display: flex; gap: 10px; }
        .message-input { flex: 1; padding: 10px; background: #1a1a1a; border: 1px solid #555; border-radius: 6px; color: #fff; }
        .send-btn { background: #0066cc; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; }
        .send-btn:hover { background: #0052a3; }
        .suggestion-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
        .chip { background: #333; border: 1px solid #555; color: #fff; padding: 6px 12px; border-radius: 15px; cursor: pointer; font-size: 12px; }
        .chip:hover { background: #444; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 ClaireDev Lightweight</h1>
        <p>Efficient AI Development Tool</p>
    </div>
    
    <div class="chat-container">
        <div class="messages" id="messages">
            <div class="assistant-message">
                👋 Welcome! What would you like to build today?
            </div>
            <div class="suggestion-chips">
                <div class="chip" onclick="sendSuggestion('Build a simple React app')">React App</div>
                <div class="chip" onclick="sendSuggestion('Create a Python API')">Python API</div>
                <div class="chip" onclick="sendSuggestion('Make a todo list')">Todo App</div>
            </div>
        </div>
        
        <div class="input-container">
            <div class="input-group">
                <input type="text" id="messageInput" class="message-input" placeholder="What do you want to build?" />
                <button class="send-btn" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        let conversation = [];
        
        function sendSuggestion(text) {
            document.getElementById('messageInput').value = text;
            sendMessage();
        }
        
        function addMessage(content, type) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            input.value = '';
            addMessage(message, 'user');
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        conversation: conversation,
                        session_id: 'session_' + Date.now(),
                        ai_settings: { model: 'gpt-3.5-turbo', temperature: 0.7, maxTokens: 1000 }
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    addMessage(data.response, 'assistant');
                    conversation.push({content: message, type: 'user'});
                    conversation.push({content: data.response, type: 'assistant'});
                }
            } catch (error) {
                addMessage('Error: ' + error.message, 'assistant');
            }
        }
        
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
"""
