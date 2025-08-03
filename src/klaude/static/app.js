class KlaudeWebClient {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 5000;
        this.sessionId = null;
        this.toolCalls = new Map();
        this.nestedTasks = new Map();
        
        this.elements = {
            conversation: document.getElementById('conversation'),
            connectionStatus: document.getElementById('connection-status'),
            connectionText: document.getElementById('connection-text'),
            sessionIdElement: document.getElementById('session-id')
        };
        
        this.connect();
    }
    
    connect() {
        // Use wss:// for https, ws:// for http
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => this.onOpen();
        this.ws.onclose = () => this.onClose();
        this.ws.onmessage = (event) => this.onMessage(event);
        this.ws.onerror = (error) => this.onError(error);
    }
    
    onOpen() {
        console.log('WebSocket connected');
        this.updateConnectionStatus(true);
    }
    
    onClose() {
        console.log('WebSocket disconnected');
        this.updateConnectionStatus(false);
        
        // Attempt to reconnect
        setTimeout(() => this.connect(), this.reconnectInterval);
    }
    
    onError(error) {
        console.error('WebSocket error:', error);
    }
    
    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        } catch (error) {
            console.error('Failed to parse message:', error);
        }
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'init':
                this.handleInit(message.data);
                break;
            case 'user_message':
                this.addUserMessage(message.data);
                break;
            case 'assistant_message':
                this.addAssistantMessage(message.data);
                break;
            case 'tool_call':
                this.addToolCall(message.data);
                break;
            case 'tool_result':
                this.updateToolResult(message.data);
                break;
            case 'task_start':
                this.handleTaskStart(message.data);
                break;
            case 'task_end':
                this.handleTaskEnd(message.data);
                break;
        }
        
        // Auto-scroll to bottom
        this.scrollToBottom();
    }
    
    handleInit(data) {
        this.sessionId = data.session_id;
        this.elements.sessionIdElement.textContent = `Session: ${this.sessionId}`;
        
        // Clear conversation
        this.elements.conversation.innerHTML = '';
        
        // Replay history
        if (data.history && data.history.length > 0) {
            data.history.forEach(msg => this.handleMessage(msg));
        } else {
            this.showWelcomeMessage();
        }
    }
    
    showWelcomeMessage() {
        this.elements.conversation.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to Klaude</h2>
                <p>Waiting for conversation to start...</p>
            </div>
        `;
    }
    
    addUserMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="message-header">
                <span>User</span>
            </div>
            <div class="message-content">
                ${this.escapeHtml(data.content)}
            </div>
        `;
        
        this.appendToConversation(messageDiv);
    }
    
    addAssistantMessage(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        
        // Parse markdown content
        const htmlContent = marked.parse(data.content || '');
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span>Assistant</span>
            </div>
            <div class="message-content">
                ${htmlContent}
            </div>
        `;
        
        this.appendToConversation(messageDiv);
        
        // Highlight code blocks
        messageDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    
    addToolCall(data) {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'tool-call';
        toolDiv.id = `tool-${data.id}`;
        
        const toolHeader = document.createElement('div');
        toolHeader.className = 'tool-header';
        toolHeader.onclick = () => this.toggleToolBody(data.id);
        
        const description = data.description ? ` (${data.description})` : '';
        
        toolHeader.innerHTML = `
            <span class="tool-name">${data.tool_name}${description}</span>
            <span class="tool-status running">
                <span class="spinner"></span>
                Running
            </span>
        `;
        
        const toolBody = document.createElement('div');
        toolBody.className = 'tool-body';
        toolBody.id = `tool-body-${data.id}`;
        
        // Format and display tool arguments
        const argsHtml = this.formatJson(data.tool_args);
        toolBody.innerHTML = `
            <div class="tool-section">
                <div class="tool-section-title">Input Parameters</div>
                <div class="tool-content">
                    <pre><code class="language-json">${argsHtml}</code></pre>
                </div>
            </div>
        `;
        
        toolDiv.appendChild(toolHeader);
        toolDiv.appendChild(toolBody);
        
        // Store reference
        this.toolCalls.set(data.id, toolDiv);
        
        // Append to appropriate parent
        if (data.parent_task_id && this.nestedTasks.has(data.parent_task_id)) {
            const parentTask = this.nestedTasks.get(data.parent_task_id);
            parentTask.appendChild(toolDiv);
        } else {
            this.appendToConversation(toolDiv);
        }
        
        // Highlight code
        toolBody.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
    
    updateToolResult(data) {
        const toolDiv = this.toolCalls.get(data.id);
        if (!toolDiv) return;
        
        const header = toolDiv.querySelector('.tool-header');
        const statusSpan = header.querySelector('.tool-status');
        const toolBody = toolDiv.querySelector('.tool-body');
        
        // Update status
        if (data.error) {
            statusSpan.className = 'tool-status error';
            statusSpan.innerHTML = 'Error';
        } else {
            statusSpan.className = 'tool-status completed';
            statusSpan.innerHTML = 'Completed';
        }
        
        // Add result section
        const resultSection = document.createElement('div');
        resultSection.className = 'tool-section';
        
        if (data.error) {
            resultSection.innerHTML = `
                <div class="tool-section-title">Error</div>
                <div class="tool-content" style="color: var(--error-color);">
                    ${this.escapeHtml(data.error)}
                </div>
            `;
        } else {
            resultSection.innerHTML = `
                <div class="tool-section-title">Output</div>
                <div class="tool-content">
                    <pre>${this.escapeHtml(data.result)}</pre>
                </div>
            `;
        }
        
        toolBody.appendChild(resultSection);
    }
    
    handleTaskStart(data) {
        const taskDiv = document.createElement('div');
        taskDiv.className = 'nested-task';
        taskDiv.id = `task-${data.id}`;
        
        const taskHeader = document.createElement('div');
        taskHeader.className = 'message-header';
        taskHeader.innerHTML = `<span>Task: ${data.description}</span>`;
        
        taskDiv.appendChild(taskHeader);
        
        // Store reference
        this.nestedTasks.set(data.id, taskDiv);
        
        // Append to appropriate parent
        if (data.parent_task_id && this.nestedTasks.has(data.parent_task_id)) {
            const parentTask = this.nestedTasks.get(data.parent_task_id);
            parentTask.appendChild(taskDiv);
        } else {
            this.appendToConversation(taskDiv);
        }
    }
    
    handleTaskEnd(data) {
        // Task ended, no specific action needed
    }
    
    toggleToolBody(toolId) {
        const toolBody = document.getElementById(`tool-body-${toolId}`);
        if (toolBody) {
            toolBody.classList.toggle('collapsed');
        }
    }
    
    appendToConversation(element) {
        // Remove welcome message if it exists
        const welcomeMsg = this.elements.conversation.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        this.elements.conversation.appendChild(element);
    }
    
    updateConnectionStatus(connected) {
        if (connected) {
            this.elements.connectionStatus.className = 'status-indicator connected';
            this.elements.connectionText.textContent = 'Connected';
        } else {
            this.elements.connectionStatus.className = 'status-indicator disconnected';
            this.elements.connectionText.textContent = 'Disconnected';
        }
    }
    
    scrollToBottom() {
        this.elements.conversation.scrollTop = this.elements.conversation.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatJson(obj) {
        try {
            return JSON.stringify(obj, null, 2);
        } catch {
            return String(obj);
        }
    }
}

// Initialize client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new KlaudeWebClient();
});