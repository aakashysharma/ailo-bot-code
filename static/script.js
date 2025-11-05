// ===== Global State =====
let isAiloReady = false;
let isProcessing = false;

// ===== DOM Elements =====
const elements = {
    statusBanner: null,
    chatMessages: null,
    userInput: null,
    sendBtn: null,
    clearBtn: null,
    saveBtn: null,
    statsBtn: null,
    statsModal: null,
    statsContent: null
};

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements
    elements.statusBanner = document.getElementById('statusBanner');
    elements.chatMessages = document.getElementById('chatMessages');
    elements.userInput = document.getElementById('userInput');
    elements.sendBtn = document.getElementById('sendBtn');
    elements.clearBtn = document.getElementById('clearBtn');
    elements.saveBtn = document.getElementById('saveBtn');
    elements.statsBtn = document.getElementById('statsBtn');
    elements.statsModal = document.getElementById('statsModal');
    elements.statsContent = document.getElementById('statsContent');

    // Setup event listeners
    setupEventListeners();

    // Check AILO status
    checkAiloStatus();

    // Auto-resize textarea
    elements.userInput.addEventListener('input', autoResizeTextarea);
});

// ===== Event Listeners Setup =====
function setupEventListeners() {
    // Send message on button click
    elements.sendBtn.addEventListener('click', sendMessage);

    // Send message on Enter (Shift+Enter for new line)
    elements.userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Enable/disable send button based on input
    elements.userInput.addEventListener('input', () => {
        const hasText = elements.userInput.value.trim().length > 0;
        elements.sendBtn.disabled = !hasText || !isAiloReady || isProcessing;
    });

    // Clear conversation
    elements.clearBtn.addEventListener('click', clearConversation);

    // Save conversation
    elements.saveBtn.addEventListener('click', saveConversation);

    // Show stats
    elements.statsBtn.addEventListener('click', showStats);

    // Close modal
    const modalClose = elements.statsModal.querySelector('.modal-close');
    modalClose.addEventListener('click', () => {
        elements.statsModal.classList.remove('active');
    });

    // Close modal on background click
    elements.statsModal.addEventListener('click', (e) => {
        if (e.target === elements.statsModal) {
            elements.statsModal.classList.remove('active');
        }
    });
}

// ===== Status Check =====
async function checkAiloStatus() {
    try {
        updateStatus('loading', '⏳', 'Laster AILO...');
        
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.ready) {
            isAiloReady = true;
            updateStatus('ready', '✅', `AILO er klar! (${data.documents} dokumenter lastet)`);
            elements.sendBtn.disabled = false;
        } else {
            updateStatus('error', '❌', 'AILO kunne ikke lastes. Prøv å laste siden på nytt.');
        }
    } catch (error) {
        console.error('Status check error:', error);
        updateStatus('error', '❌', 'Kunne ikke koble til AILO serveren.');
    }
}

function updateStatus(type, icon, text) {
    elements.statusBanner.className = `status-banner status-${type}`;
    elements.statusBanner.innerHTML = `
        <span class="status-icon">${icon}</span>
        <span class="status-text">${text}</span>
    `;
}

// ===== Send Message =====
async function sendMessage() {
    const message = elements.userInput.value.trim();
    
    if (!message || !isAiloReady || isProcessing) {
        return;
    }

    // Disable input
    isProcessing = true;
    elements.sendBtn.disabled = true;
    elements.userInput.disabled = true;

    // Add user message to chat
    addMessage('user', message);

    // Clear input
    elements.userInput.value = '';
    autoResizeTextarea();

    // Show loading indicator
    const loadingId = addLoadingMessage();

    try {
        // Send to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        // Remove loading indicator
        removeLoadingMessage(loadingId);

        if (data.success) {
            // Add assistant response
            addMessage('assistant', data.response);
        } else {
            // Show error
            addMessage('system', `❌ Feil: ${data.error}`);
        }
    } catch (error) {
        console.error('Send message error:', error);
        removeLoadingMessage(loadingId);
        addMessage('system', '❌ Kunne ikke sende melding. Prøv igjen.');
    } finally {
        // Re-enable input
        isProcessing = false;
        elements.userInput.disabled = false;
        elements.sendBtn.disabled = elements.userInput.value.trim().length === 0;
        elements.userInput.focus();
    }
}

// ===== Message Display =====
function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    let avatarEmoji = '🔮';
    if (type === 'user') avatarEmoji = '👤';
    else if (type === 'system') avatarEmoji = 'ℹ️';

    // Format content (preserve line breaks, etc.)
    const formattedContent = formatMessageContent(content);

    if (type === 'system') {
        messageDiv.innerHTML = `
            <div class="message-content">${formattedContent}</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatarEmoji}</div>
            <div class="message-content">${formattedContent}</div>
        `;
    }

    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function formatMessageContent(content) {
    // Convert markdown-like formatting to HTML
    let formatted = content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
    
    return formatted;
}

function addLoadingMessage() {
    const loadingId = 'loading-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message loading-message';
    messageDiv.id = loadingId;
    messageDiv.innerHTML = `
        <div class="message-avatar">🔮</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return loadingId;
}

function removeLoadingMessage(loadingId) {
    const loadingMsg = document.getElementById(loadingId);
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// ===== Clear Conversation =====
async function clearConversation() {
    if (!confirm('Er du sikker på at du vil tømme samtalen?')) {
        return;
    }

    try {
        const response = await fetch('/api/clear', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            // Remove all messages except welcome message
            const messages = elements.chatMessages.querySelectorAll('.message:not(.system-message)');
            messages.forEach(msg => msg.remove());
            
            addMessage('system', '✅ Samtalen er tømt. Historikken er nullstilt.');
        } else {
            addMessage('system', `❌ Kunne ikke tømme samtalen: ${data.error}`);
        }
    } catch (error) {
        console.error('Clear conversation error:', error);
        addMessage('system', '❌ Kunne ikke tømme samtalen. Prøv igjen.');
    }
}

// ===== Save Conversation =====
async function saveConversation() {
    try {
        const response = await fetch('/api/save', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            addMessage('system', `✅ Samtalen er lagret til: <code>${data.filename}</code>`);
        } else {
            addMessage('system', `❌ Kunne ikke lagre samtalen: ${data.error}`);
        }
    } catch (error) {
        console.error('Save conversation error:', error);
        addMessage('system', '❌ Kunne ikke lagre samtalen. Prøv igjen.');
    }
}

// ===== Show Stats =====
async function showStats() {
    elements.statsModal.classList.add('active');
    elements.statsContent.innerHTML = '<p>Laster statistikk...</p>';

    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        if (data.success) {
            elements.statsContent.innerHTML = `
                <div class="stat-item">
                    <h3>📚 Dokumenter i kunnskapsbase</h3>
                    <div class="stat-value">${data.stats.total_documents.toLocaleString('no-NO')}</div>
                </div>
                <div class="stat-item">
                    <h3>💬 Meldinger i samtale</h3>
                    <div class="stat-value">${data.stats.messages_in_history}</div>
                </div>
                <div class="stat-item">
                    <h3>🔗 Totalt antall innlastede chunks</h3>
                    <div class="stat-value">${data.stats.total_chunks.toLocaleString('no-NO')}</div>
                </div>
                <div class="stat-item">
                    <h3>⚙️ LLM Modell</h3>
                    <div class="stat-value" style="font-size: 18px;">${data.stats.model || 'Gemma 3n'}</div>
                </div>
                <div class="stat-item">
                    <h3>🌡️ Temperatur</h3>
                    <div class="stat-value">${data.stats.temperature || 0.3}</div>
                </div>
                <div class="stat-item">
                    <h3>📊 Top K verdier hentet</h3>
                    <div class="stat-value">${data.stats.top_k || 10}</div>
                </div>
            `;
        } else {
            elements.statsContent.innerHTML = `<p>❌ Kunne ikke laste statistikk: ${data.error}</p>`;
        }
    } catch (error) {
        console.error('Stats error:', error);
        elements.statsContent.innerHTML = '<p>❌ Kunne ikke laste statistikk. Prøv igjen.</p>';
    }
}

// ===== Auto-resize Textarea =====
function autoResizeTextarea() {
    const textarea = elements.userInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}
