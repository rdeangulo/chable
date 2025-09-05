// Residencias Chable AI Handler Testing Interface
// Main JavaScript file for handling all interactions and API calls

class ResidenciasChableApp {
    constructor() {
        this.currentSection = 'chat-widget';
        this.chatHistory = [];
        this.conversationId = this.generateConversationId();
        this.isProcessing = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupNavigation();
        this.loadSettings();
        this.addLogEntry('info', 'AI Handler Testing Interface initialized');
    }

    setupEventListeners() {
        // Chat functionality
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const clearChatButton = document.getElementById('clearChat');
        const exportChatButton = document.getElementById('exportChat');

        if (messageInput && sendButton) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            sendButton.addEventListener('click', () => this.sendMessage());
        }

        if (clearChatButton) {
            clearChatButton.addEventListener('click', () => this.clearChat());
        }

        if (exportChatButton) {
            exportChatButton.addEventListener('click', () => this.exportChat());
        }

        // Settings
        const saveSettingsButton = document.getElementById('saveSettings');
        const resetSettingsButton = document.getElementById('resetSettings');

        if (saveSettingsButton) {
            saveSettingsButton.addEventListener('click', () => this.saveSettings());
        }

        if (resetSettingsButton) {
            resetSettingsButton.addEventListener('click', () => this.resetSettings());
        }

        // Logs
        const clearLogsButton = document.getElementById('clearLogs');
        if (clearLogsButton) {
            clearLogsButton.addEventListener('click', () => this.clearLogs());
        }
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const contentSections = document.querySelectorAll('.content-section');

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetSection = link.getAttribute('href').substring(1);
                this.showSection(targetSection);
            });
        });
    }

    showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Remove active class from all nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        // Show target section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
        }

        // Activate corresponding nav link
        const activeLink = document.querySelector(`[href="#${sectionId}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        this.currentSection = sectionId;
        this.addLogEntry('info', `Switched to ${sectionId} section`);
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        if (!message || this.isProcessing) return;

        this.isProcessing = true;
        this.addMessageToChat('user', message);
        messageInput.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await this.processMessage(message);
            this.hideTypingIndicator();
            this.addMessageToChat('assistant', response);
            this.addLogEntry('info', `Message processed successfully: "${message}"`);
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessageToChat('assistant', 'Lo siento, hubo un error procesando tu mensaje. Por favor, intenta de nuevo.');
            this.addLogEntry('error', `Error processing message: ${error.message}`);
        } finally {
            this.isProcessing = false;
        }
    }

    async processMessage(message) {
        const response = await fetch('/web-widget/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                Body: message,
                From: this.conversationId,
                To: 'web-widget',
                Platform: 'web'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.response || 'No response received';
    }

    addMessageToChat(role, content) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        let icon = '';
        if (role === 'user') {
            icon = '<i class="fas fa-user"></i>';
        } else if (role === 'assistant') {
            icon = '<i class="fas fa-robot"></i>';
        } else if (role === 'system') {
            icon = '<i class="fas fa-info-circle"></i>';
        }

        messageContent.innerHTML = `${icon}<p>${this.escapeHtml(content)}</p>`;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.getCurrentTime();

        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Store in history
        this.chatHistory.push({
            role,
            content,
            timestamp: new Date().toISOString()
        });
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-robot"></i>
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        const systemMessage = chatMessages.querySelector('.message.system');
        
        chatMessages.innerHTML = '';
        if (systemMessage) {
            chatMessages.appendChild(systemMessage);
        }
        
        this.chatHistory = [];
        this.conversationId = this.generateConversationId();
        this.addLogEntry('info', 'Chat cleared');
    }

    exportChat() {
        if (this.chatHistory.length === 0) {
            alert('No hay conversación para exportar.');
            return;
        }

        const exportData = {
            conversationId: this.conversationId,
            timestamp: new Date().toISOString(),
            messages: this.chatHistory
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
            type: 'application/json'
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-export-${this.conversationId}-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.addLogEntry('info', 'Chat exported successfully');
    }

    // AI Function Testing Methods
    async testSearchProperties() {
        const query = document.getElementById('searchQuery').value.trim();
        const maxResults = document.getElementById('maxResults').value;

        if (!query) {
            alert('Por favor ingresa una consulta de búsqueda.');
            return;
        }

        try {
            this.addLogEntry('info', `Testing search_properties function with query: "${query}"`);
            
            // Simulate function call
            const result = await this.simulateFunctionCall('search_properties', {
                query,
                max_results: parseInt(maxResults)
            });

            this.addLogEntry('info', `Function test completed: ${result}`);
            alert(`Función probada exitosamente. Resultado: ${result}`);
        } catch (error) {
            this.addLogEntry('error', `Function test failed: ${error.message}`);
            alert(`Error probando la función: ${error.message}`);
        }
    }

    async testSendPhoto() {
        const category = document.getElementById('photoCategory').value;
        const message = document.getElementById('photoMessage').value.trim();

        try {
            this.addLogEntry('info', `Testing enviar_foto function for category: ${category}`);
            
            const result = await this.simulateFunctionCall('enviar_foto', {
                categoria: category,
                mensaje_acompañante: message
            });

            this.addLogEntry('info', `Function test completed: ${result}`);
            alert(`Función probada exitosamente. Resultado: ${result}`);
        } catch (error) {
            this.addLogEntry('error', `Function test failed: ${error.message}`);
            alert(`Error probando la función: ${error.message}`);
        }
    }

    async testCaptureCustomer() {
        const name = document.getElementById('customerName').value.trim();
        const phone = document.getElementById('customerPhone').value.trim();
        const email = document.getElementById('customerEmail').value.trim();

        if (!name || !phone) {
            alert('Por favor ingresa al menos el nombre y teléfono.');
            return;
        }

        try {
            this.addLogEntry('info', `Testing capture_customer_info function for: ${name}`);
            
            const result = await this.simulateFunctionCall('capture_customer_info', {
                nombre: name,
                telefono: phone,
                email: email
            });

            this.addLogEntry('info', `Function test completed: ${result}`);
            alert(`Función probada exitosamente. Resultado: ${result}`);
        } catch (error) {
            this.addLogEntry('error', `Function test failed: ${error.message}`);
            alert(`Error probando la función: ${error.message}`);
        }
    }

    async testSendBrochure() {
        const phone = document.getElementById('brochurePhone').value.trim();
        const type = document.getElementById('brochureType').value;

        if (!phone) {
            alert('Por favor ingresa un número de teléfono.');
            return;
        }

        try {
            this.addLogEntry('info', `Testing send_brochure function for: ${phone}`);
            
            const result = await this.simulateFunctionCall('send_brochure', {
                telefono: phone,
                tipo_propiedad: type
            });

            this.addLogEntry('info', `Function test completed: ${result}`);
            alert(`Función probada exitosamente. Resultado: ${result}`);
        } catch (error) {
            this.addLogEntry('error', `Function test failed: ${error.message}`);
            alert(`Error probando la función: ${error.message}`);
        }
    }

    async testVectorStore() {
        const query = document.getElementById('vectorQuery').value.trim();
        const resultsContainer = document.getElementById('vectorResults');

        if (!query) {
            alert('Por favor ingresa una consulta para buscar.');
            return;
        }

        try {
            this.addLogEntry('info', `Testing vector store with query: "${query}"`);
            
            // Simulate vector store call
            const results = await this.simulateVectorStoreCall(query);
            
            this.displayVectorStoreResults(results);
            this.addLogEntry('info', `Vector store test completed with ${results.length} results`);
        } catch (error) {
            this.addLogEntry('error', `Vector store test failed: ${error.message}`);
            resultsContainer.innerHTML = `<p class="error">Error: ${error.message}</p>`;
        }
    }

    async simulateFunctionCall(functionName, parameters) {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Return simulated response based on function
        switch (functionName) {
            case 'search_properties':
                return `Búsqueda simulada completada para "${parameters.query}" con ${parameters.max_results} resultados`;
            case 'enviar_foto':
                return `Foto enviada para categoría: ${parameters.categoria}`;
            case 'capture_customer_info':
                return `Información capturada para: ${parameters.nombre} (${parameters.telefono})`;
            case 'send_brochure':
                return `Folleto enviado al: ${parameters.telefono}`;
            default:
                return `Función ${functionName} ejecutada con éxito`;
        }
    }

    async simulateVectorStoreCall(query) {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Return simulated vector store results
        return [
            {
                id: `prop_001_${Date.now()}`,
                categoria: 'apartamento',
                area: 'Playa del Carmen',
                precio: '$450,000 USD',
                descripcion: `Hermoso apartamento cerca de la playa - ${query}`,
                similarity: 0.95
            },
            {
                id: `prop_002_${Date.now()}`,
                categoria: 'casa',
                area: 'Tulum',
                precio: '$850,000 USD',
                descripcion: `Casa moderna con vista al mar - ${query}`,
                similarity: 0.87
            },
            {
                id: `prop_003_${Date.now()}`,
                categoria: 'terreno',
                area: 'Puerto Morelos',
                precio: '$250,000 USD',
                descripcion: `Terreno ideal para desarrollo - ${query}`,
                similarity: 0.82
            }
        ];
    }

    displayVectorStoreResults(results) {
        const resultsContainer = document.getElementById('vectorResults');
        
        if (results.length === 0) {
            resultsContainer.innerHTML = '<p class="placeholder-text">No se encontraron resultados.</p>';
            return;
        }

        const resultsHtml = results.map(result => `
            <div class="result-item" style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                    <h4 style="margin: 0; color: #2d3748;">${result.categoria.toUpperCase()}</h4>
                    <span style="background: #667eea; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">
                        ${(result.similarity * 100).toFixed(0)}% match
                    </span>
                </div>
                <p style="margin: 0.5rem 0; color: #4a5568;"><strong>Área:</strong> ${result.area}</p>
                <p style="margin: 0.5rem 0; color: #4a5568;"><strong>Precio:</strong> ${result.precio}</p>
                <p style="margin: 0.5rem 0; color: #718096;">${result.descripcion}</p>
                <p style="margin: 0; font-size: 0.75rem; color: #a0aec0;">ID: ${result.id}</p>
            </div>
        `).join('');

        resultsContainer.innerHTML = resultsHtml;
    }

    // Settings Management
    loadSettings() {
        const settings = this.getStoredSettings();
        
        if (settings.modelSpeed) {
            document.getElementById('modelSpeed').value = settings.modelSpeed;
        }
        if (settings.maxTokens) {
            document.getElementById('maxTokens').value = settings.maxTokens;
        }
        if (settings.temperature) {
            document.getElementById('temperature').value = settings.temperature;
        }
        if (settings.storeId) {
            document.getElementById('storeId').value = settings.storeId;
        }
    }

    saveSettings() {
        const settings = {
            modelSpeed: document.getElementById('modelSpeed').value,
            maxTokens: parseInt(document.getElementById('maxTokens').value),
            temperature: parseFloat(document.getElementById('temperature').value),
            storeId: document.getElementById('storeId').value
        };

        localStorage.setItem('residenciasChableSettings', JSON.stringify(settings));
        this.addLogEntry('info', 'Settings saved successfully');
        alert('Configuración guardada exitosamente.');
    }

    resetSettings() {
        const defaultSettings = {
            modelSpeed: 'balanced',
            maxTokens: 1500,
            temperature: 0.7,
            storeId: 'residencias_chable_default'
        };

        localStorage.setItem('residenciasChableSettings', JSON.stringify(defaultSettings));
        this.loadSettings();
        this.addLogEntry('info', 'Settings reset to default');
        alert('Configuración restablecida a valores predeterminados.');
    }

    getStoredSettings() {
        const stored = localStorage.getItem('residenciasChableSettings');
        return stored ? JSON.parse(stored) : {};
    }

    // Utility Methods
    generateConversationId() {
        return 'web_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('es-MX', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    addLogEntry(level, message) {
        const logsContent = document.getElementById('logsContent');
        if (!logsContent) return;

        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level}`;
        
        const timestamp = new Date().toLocaleString('es-MX');
        logEntry.innerHTML = `
            <span class="log-time">[${timestamp}]</span>
            <span class="log-level">[${level.toUpperCase()}]</span>
            <span class="log-message">${this.escapeHtml(message)}</span>
        `;

        logsContent.appendChild(logEntry);
        logsContent.scrollTop = logsContent.scrollHeight;

        // Keep only last 100 log entries
        const entries = logsContent.querySelectorAll('.log-entry');
        if (entries.length > 100) {
            entries[0].remove();
        }
    }

    clearLogs() {
        const logsContent = document.getElementById('logsContent');
        if (logsContent) {
            logsContent.innerHTML = '';
            this.addLogEntry('info', 'Logs cleared');
        }
    }

    copyStoreId() {
        const storeIdInput = document.getElementById('storeId');
        storeIdInput.select();
        document.execCommand('copy');
        
        // Show feedback
        const copyButton = event.target;
        const originalText = copyButton.textContent;
        copyButton.textContent = 'Copiado!';
        copyButton.style.background = '#48bb78';
        
        setTimeout(() => {
            copyButton.textContent = originalText;
            copyButton.style.background = '';
        }, 2000);
        
        this.addLogEntry('info', 'Store ID copied to clipboard');
    }
}

// Global function exports for HTML onclick handlers
window.testSearchProperties = function() {
    app.testSearchProperties();
};

window.testSendPhoto = function() {
    app.testSendPhoto();
};

window.testCaptureCustomer = function() {
    app.testCaptureCustomer();
};

window.testSendBrochure = function() {
    app.testSendBrochure();
};

window.testVectorStore = function() {
    app.testVectorStore();
};

window.saveSettings = function() {
    app.saveSettings();
};

window.resetSettings = function() {
    app.resetSettings();
};

window.clearLogs = function() {
    app.clearLogs();
};

window.copyStoreId = function() {
    app.copyStoreId();
};

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ResidenciasChableApp();
});

// Add some CSS for typing indicator
const style = document.createElement('style');
style.textContent = `
    .typing-dots {
        display: flex;
        gap: 4px;
        align-items: center;
    }
    
    .typing-dots span {
        width: 8px;
        height: 8px;
        background: #667eea;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
    .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    
    .result-item:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: box-shadow 0.2s ease;
    }
    
    .error {
        color: #e53e3e;
        text-align: center;
        font-weight: 500;
    }
`;
document.head.appendChild(style);
