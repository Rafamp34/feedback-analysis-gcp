// =====================================================
// CHATBOT FUNCTIONALITY
// =====================================================

const chatbot = {
    container: null,
    messages: null,
    input: null,
    sendBtn: null,
    toggleBtn: null,
    isOpen: false,
    
    init() {
        console.log('🤖 Inicializando chatbot...');
        
        this.container = document.getElementById('chatbot-container');
        this.messages = document.getElementById('chatbot-messages');
        this.input = document.getElementById('chatbot-input');
        this.sendBtn = document.getElementById('chatbot-send');
        this.toggleBtn = document.getElementById('chatbot-toggle');
        
        if (!this.container || !this.messages || !this.input || !this.sendBtn || !this.toggleBtn) {
            console.error('❌ Error: No se encontraron elementos del chatbot');
            return;
        }
        
        console.log('✅ Elementos del chatbot encontrados');
        this.attachEventListeners();
    },
    
    attachEventListeners() {
        console.log('🔗 Añadiendo event listeners...');
        
        // Toggle chatbot
        this.toggleBtn.addEventListener('click', () => {
            console.log('👆 Click en toggle');
            this.toggle();
        });
        
        // Cerrar chatbot
        const closeBtn = document.getElementById('chatbot-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                console.log('👆 Click en cerrar');
                this.close();
            });
        }
        
        // Minimizar chatbot
        const minimizeBtn = document.getElementById('chatbot-minimize');
        if (minimizeBtn) {
            minimizeBtn.addEventListener('click', () => {
                console.log('👆 Click en minimizar');
                this.minimize();
            });
        }
        
        // Enviar mensaje
        this.sendBtn.addEventListener('click', () => {
            console.log('👆 Click en enviar');
            this.sendMessage();
        });
        
        // Enter para enviar
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                console.log('⌨️ Enter presionado');
                this.sendMessage();
            }
        });
        
        // Sugerencias rápidas
        const suggestionBtns = document.querySelectorAll('.suggestion-btn');
        console.log(`📌 Encontrados ${suggestionBtns.length} botones de sugerencia`);
        
        suggestionBtns.forEach((btn, index) => {
            const message = btn.getAttribute('data-message');
            console.log(`  Botón ${index + 1}: "${message}"`);
            
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log(`👆 Click en sugerencia: "${message}"`);
                this.input.value = message;
                this.sendMessage();
            });
        });
        
        console.log('✅ Event listeners añadidos correctamente');
    },
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    },
    
    open() {
        console.log('📖 Abriendo chatbot');
        this.container.classList.remove('hidden');
        this.container.classList.remove('minimized');
        this.isOpen = true;
        this.input.focus();
        
        // Ocultar el badge de "nuevo"
        const badge = this.toggleBtn.querySelector('.chatbot-badge');
        if (badge) {
            badge.style.display = 'none';
        }
    },
    
    close() {
        console.log('📕 Cerrando chatbot');
        this.container.classList.add('hidden');
        this.isOpen = false;
    },
    
    minimize() {
        console.log('➖ Minimizando chatbot');
        this.container.classList.toggle('minimized');
    },
    
    async sendMessage() {
        const message = this.input.value.trim();
        
        console.log(`📤 Enviando mensaje: "${message}"`);
        
        if (!message) {
            console.log('⚠️ Mensaje vacío, cancelando');
            return;
        }
        
        // Añadir mensaje del usuario
        this.addMessage(message, 'user');
        
        // Limpiar input
        this.input.value = '';
        
        // Mostrar indicador de escritura
        this.showTypingIndicator();
        
        try {
            // Enviar a la API
            console.log('🌐 Llamando a la API...');
            const response = await this.sendToAPI(message);
            
            console.log('✅ Respuesta recibida:', response);
            
            // Remover indicador de escritura
            this.removeTypingIndicator();
            
            // Añadir respuesta del bot
            this.addMessage(response, 'bot');
            
        } catch (error) {
            console.error('❌ Error al enviar mensaje:', error);
            this.removeTypingIndicator();
            this.addMessage('Lo siento, hubo un error. Por favor intenta de nuevo.', 'bot');
        }
    },
    
    async sendToAPI(message) {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('session_id', this.getSessionId());
        
        const response = await fetch('/api/chatbot/message', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error en la respuesta del servidor');
        }
        
        const data = await response.json();
        return data.response;
    },
    
    addMessage(text, sender) {
        console.log(`💬 Añadiendo mensaje ${sender}: "${text.substring(0, 50)}..."`);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'bot' 
            ? '<i class="fas fa-robot"></i>' 
            : '<i class="fas fa-user"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        // Convertir saltos de línea a <br> y procesar el texto
        const formattedText = text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        content.innerHTML = `<p>${formattedText}</p>`;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.messages.appendChild(messageDiv);
        this.scrollToBottom();
    },
    
    showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'chatbot-message bot-message';
        indicator.id = 'typing-indicator';
        
        indicator.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        this.messages.appendChild(indicator);
        this.scrollToBottom();
    },
    
    removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    },
    
    scrollToBottom() {
        this.messages.scrollTop = this.messages.scrollHeight;
    },
    
    getSessionId() {
        let sessionId = localStorage.getItem('chatbot_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chatbot_session_id', sessionId);
        }
        return sessionId;
    }
};

// Inicializar chatbot cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('📄 DOM cargado, inicializando chatbot');
        chatbot.init();
    });
} else {
    // DOM ya está listo
    console.log('📄 DOM ya estaba listo, inicializando chatbot');
    chatbot.init();
}