/**
 * EventEase — Messaging JS
 * Handles real-time polling, sending, and UI updates
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Thread Initialization & Scroll
    const messagesArea = document.getElementById('messagesArea');
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    
    function scrollToBottom(smooth = false) {
        if (!messagesArea) return;
        if (smooth) {
            messagesArea.scrollTo({ top: messagesArea.scrollHeight, behavior: 'smooth' });
        } else {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    }

    if (messagesArea) {
        scrollToBottom();
    }

    // 2. Input Handling
    if (messageInput) {
        messageInput.addEventListener('input', () => {
            sendBtn.disabled = messageInput.value.trim().length === 0;
        });

        // Enter to send (but not shift+enter)
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!sendBtn.disabled) messageForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    // 3. Send Message via AJAX
    if (messageForm) {
        messageForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = messageInput.value.trim();
            if (!text) return;
            
            const chatContainer = document.querySelector('.chat-container');
            const convId = chatContainer.dataset.convId;
            
            // Optimistic UI update could go here, but let's wait for server for simplicity & accuracy
            messageInput.value = '';
            sendBtn.disabled = true;
            
            try {
                const res = await fetch('/messages/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ conversation_id: convId, message: text })
                });
                const data = await res.json();
                
                if (data.status === 'ok') {
                    // Force a poll immediately to get the new message
                    pollMessages();
                }
            } catch (err) {
                console.error("Failed to send message", err);
            }
        });
    }

    // 4. Polling for new messages
    let pollingInterval;
    
    async function pollMessages() {
        const chatContainer = document.querySelector('.chat-container');
        if (!chatContainer || !messagesArea) return;
        
        const convId = chatContainer.dataset.convId;
        // Find highest message ID currently on screen
        const msgElements = messagesArea.querySelectorAll('.message-wrapper');
        let lastId = 0;
        if (msgElements.length > 0) {
            lastId = msgElements[msgElements.length - 1].dataset.msgId;
        }
        
        try {
            const res = await fetch(`/messages/${convId}?last_id=${lastId}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await res.json();
            
            if (data.html && data.html.trim() !== '') {
                // Determine if we are at the bottom before adding
                const isAtBottom = messagesArea.scrollHeight - messagesArea.scrollTop <= messagesArea.clientHeight + 50;
                
                messagesArea.insertAdjacentHTML('beforeend', data.html);
                bindDeleteButtons();
                
                if (isAtBottom) scrollToBottom(true);
            }
        } catch (err) {
            console.error("Polling error", err);
        }
    }

    if (document.querySelector('.chat-container')) {
        pollingInterval = setInterval(pollMessages, 5000);
    }

    // 5. Delete Message
    function bindDeleteButtons() {
        document.querySelectorAll('.delete-msg-btn').forEach(btn => {
            // Remove existing to prevent duplicates
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', async (e) => {
                const msgId = newBtn.dataset.id;
                if (!confirm('Delete this message?')) return;
                
                try {
                    const res = await fetch(`/messages/delete/${msgId}`, { method: 'POST' });
                    const data = await res.json();
                    if (data.status === 'ok') {
                        const bubble = newBtn.closest('.message-bubble');
                        bubble.innerHTML = '<span class="deleted-text"><i>This message was deleted</i></span>';
                    }
                } catch (err) {
                    console.error("Failed to delete", err);
                }
            });
        });
    }
    
    bindDeleteButtons();

    // 6. Search conversations
    const searchInput = document.getElementById('convSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const val = e.target.value.toLowerCase();
            document.querySelectorAll('.conv-item').forEach(item => {
                const name = item.querySelector('h4').textContent.toLowerCase();
                const event = item.querySelector('.conv-event-chip') ? item.querySelector('.conv-event-chip').textContent.toLowerCase() : '';
                
                if (name.includes(val) || event.includes(val)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
});
