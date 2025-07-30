// Simple chat functionality for satellite tracking app

class ChatBot {
    constructor() {
        this.chatLog = document.getElementById('chat-log');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-button');
        this.chatResponse = document.getElementById('chat-response');
        
        this.initializeEventListeners();
        this.addWelcomeMessage();
    }
    
    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Enter key press
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }
    
    addWelcomeMessage() {
        this.addMessageToLog('bot', 'Hello! I\'m your satellite tracking assistant. Ask me about satellites, orbits, or how to use this tracker!');
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        // Add user message to log
        this.addMessageToLog('user', message);
        this.chatInput.value = '';
        
        // Show loading
        this.addMessageToLog('bot', 'Thinking...', true);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            // Remove loading message
            this.removeLoadingMessage();
            
            if (data.success) {
                this.addMessageToLog('bot', data.response);
            } else {
                this.addMessageToLog('bot', 'Sorry, I encountered an error. Please try again.');
            }
            
        } catch (error) {
            console.error('Chat error:', error);
            this.removeLoadingMessage();
            this.addMessageToLog('bot', 'Sorry, I cannot connect right now. Please try again later.');
        }
    }
    
    addMessageToLog(sender, message, isLoading = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message${isLoading ? ' loading' : ''}`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content user-msg">
                    <strong>You:</strong> ${this.escapeHtml(message)}
                    <small class="timestamp">${timestamp}</small>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content bot-msg">
                    <strong>🤖 Assistant:</strong> ${this.escapeHtml(message)}
                    <small class="timestamp">${timestamp}</small>
                </div>
            `;
        }
        
        this.chatLog.appendChild(messageDiv);
        this.chatLog.scrollTop = this.chatLog.scrollHeight;
    }
    
    removeLoadingMessage() {
        const loadingMessage = this.chatLog.querySelector('.loading');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/\n/g, '<br>');
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('chat-log')) {
        new ChatBot();
    }
});