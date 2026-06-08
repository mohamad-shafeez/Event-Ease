/**
 * EventEase AI Interactions
 * Handles chat widget, form generation, smart search, and moderation.
 */

document.addEventListener('DOMContentLoaded', () => {

    /* ── Floating Chat Panel ──────────────────────────────── */
    const chatWidget = document.getElementById('ai-chat-widget');
    if (chatWidget) {
        const toggleBtn = document.getElementById('ai-toggle-btn');
        const closeBtn = document.getElementById('ai-close-btn');
        const sendBtn = document.getElementById('ai-send-btn');
        const inputField = document.getElementById('ai-input');
        const messagesDiv = document.getElementById('ai-messages');
        const typingInd = document.getElementById('ai-typing');

        let role = chatWidget.dataset.role || 'user';
        let hasInitialized = false;

        // Open/Close
        toggleBtn.addEventListener('click', () => {
            chatWidget.classList.remove('ai-widget-collapsed');
            chatWidget.classList.add('ai-widget-expanded');
            if (!hasInitialized) {
                let greeting = "Hi! I can help you find events, answer questions, or explain ticket details.";
                if (role === 'admin') greeting = "Hi! I can help you analyze platform data, moderate events, or answer questions.";
                if (role === 'creator') greeting = "Hi! I can help write event descriptions, suggest pricing, or create promo copy.";
                appendMessage(greeting, 'bot');
                hasInitialized = true;
            }
            setTimeout(() => inputField.focus(), 300);
        });

        closeBtn.addEventListener('click', () => {
            chatWidget.classList.remove('ai-widget-expanded');
            chatWidget.classList.add('ai-widget-collapsed');
        });

        // Send Message
        const sendMessage = () => {
            const text = inputField.value.trim();
            if (!text) return;

            appendMessage(text, 'user');
            inputField.value = '';
            typingInd.style.display = 'flex';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            fetch('/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            })
            .then(res => res.json())
            .then(data => {
                typingInd.style.display = 'none';
                appendMessage(data.reply, 'bot');
            })
            .catch(err => {
                typingInd.style.display = 'none';
                appendMessage("Sorry, I'm having trouble connecting right now.", 'bot');
            });
        };

        sendBtn.addEventListener('click', sendMessage);
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        function appendMessage(text, sender) {
            const div = document.createElement('div');
            div.className = `ai-bubble ${sender}`;
            div.textContent = text;
            if (typingInd && typingInd.parentNode === messagesDiv) {
                messagesDiv.insertBefore(div, typingInd);
            } else {
                messagesDiv.appendChild(div);
            }
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    }

    /* ── Creator: Generate Description ──────────────────────── */
    const btnDesc = document.getElementById('ai-gen-desc');
    const txtDesc = document.getElementById('description');
    const badgeDesc = document.getElementById('ai-desc-badge');
    
    if (btnDesc && txtDesc) {
        btnDesc.addEventListener('click', () => {
            const title = document.getElementById('title').value;
            const type = document.getElementById('event-type').value;
            const venue = document.getElementById('venue').value;
            
            btnDesc.disabled = true;
            btnDesc.textContent = "✨ Generating...";
            
            fetch('/ai/generate-description', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, type, venue })
            })
            .then(r => r.json())
            .then(data => {
                txtDesc.value = data.description;
                badgeDesc.style.display = 'block';
            })
            .finally(() => {
                btnDesc.disabled = false;
                btnDesc.textContent = "✨ Generate Description";
            });
        });
    }

    /* ── Creator: Suggest Price ─────────────────────────────── */
    const btnPrice = document.getElementById('ai-sug-price');
    const inpPrice = document.getElementById('price');
    const badgePrice = document.getElementById('ai-price-badge');

    if (btnPrice && inpPrice) {
        btnPrice.addEventListener('click', () => {
            const type = document.getElementById('event-type').value;
            const city = document.getElementById('city').value;
            const cap = document.getElementById('capacity').value;

            btnPrice.disabled = true;
            btnPrice.textContent = "💡 Thinking...";

            fetch('/ai/suggest-pricing', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, city, capacity: cap })
            })
            .then(r => r.json())
            .then(data => {
                inpPrice.value = data.price;
                badgePrice.textContent = `Gemini suggests ₹${data.price} — ${data.reason}`;
                badgePrice.style.display = 'block';
            })
            .finally(() => {
                btnPrice.disabled = false;
                btnPrice.textContent = "💡 Suggest Price";
            });
        });
    }

    /* ── Creator: Write Promo Copy ──────────────────────────── */
    const btnPromo = document.getElementById('ai-write-promo');
    if (btnPromo) {
        btnPromo.addEventListener('click', () => {
            const title = document.getElementById('title').value;
            const type = document.getElementById('event-type').value;
            const city = document.getElementById('city').value;

            btnPromo.disabled = true;
            btnPromo.textContent = "📣 Writing...";

            fetch('/ai/write-promo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, type, city })
            })
            .then(r => r.json())
            .then(data => {
                showPromoModal(data.promo_text);
            })
            .finally(() => {
                btnPromo.disabled = false;
                btnPromo.textContent = "📣 Write Promo Copy";
            });
        });
    }

    function showPromoModal(text) {
        // Create modal DOM if it doesn't exist
        let overlay = document.getElementById('ai-promo-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'ai-promo-overlay';
            overlay.className = 'ai-modal-overlay';
            overlay.innerHTML = `
                <div class="ai-modal">
                    <h3 style="display:flex;align-items:center;gap:8px"><span>✨</span> Promotional Copy</h3>
                    <p class="text-muted text-sm mt-1">Generated by Gemini AI. Ready for WhatsApp or Instagram!</p>
                    <textarea class="ai-modal-textarea" id="ai-promo-text" readonly></textarea>
                    <div style="display:flex;justify-content:flex-end;gap:12px;margin-top:24px">
                        <button class="btn btn-ghost" id="ai-promo-close">Close</button>
                        <button class="btn btn-primary" id="ai-promo-copy">📋 Copy to Clipboard</button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);

            document.getElementById('ai-promo-close').addEventListener('click', () => {
                overlay.classList.remove('active');
            });

            document.getElementById('ai-promo-copy').addEventListener('click', (e) => {
                const ta = document.getElementById('ai-promo-text');
                ta.select();
                document.execCommand('copy');
                e.target.textContent = "✅ Copied!";
                setTimeout(() => e.target.textContent = "📋 Copy to Clipboard", 2000);
            });
        }
        
        document.getElementById('ai-promo-text').value = text;
        overlay.classList.add('active');
    }

    /* ── Smart Search ───────────────────────────────────────── */
    const btnSmart = document.getElementById('ai-smart-search-btn');
    const inpSmart = document.getElementById('ai-smart-search-input');
    const stsSmart = document.getElementById('ai-smart-search-status');

    if (btnSmart && inpSmart) {
        const performSearch = () => {
            const query = inpSmart.value.trim();
            if (!query) return;

            btnSmart.disabled = true;
            stsSmart.style.display = 'block';

            fetch('/ai/smart-search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            })
            .then(r => r.json())
            .then(filters => {
                // Fill the regular filter form
                if (filters.type) {
                    const cb = document.querySelector(`input[name="type"][value="${filters.type}"]`);
                    if (cb) cb.checked = true;
                }
                if (filters.city) {
                    document.getElementById('filter-city').value = filters.city;
                }
                if (filters.price_range) {
                    if (filters.price_range.toLowerCase() === 'free') {
                        document.querySelector('input[name="price"][value="free"]').checked = true;
                    }
                }
                // Auto submit the form
                document.getElementById('filter-form').submit();
            })
            .catch(() => {
                stsSmart.textContent = 'Could not interpret. Try again.';
                btnSmart.disabled = false;
            });
        };

        btnSmart.addEventListener('click', performSearch);
        inpSmart.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch();
        });
    }

    /* ── Admin: AI Moderation ───────────────────────────────── */
    document.querySelectorAll('.ai-moderate-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.dataset.id;
            const badge = document.getElementById(`mod-badge-${id}`);
            
            this.disabled = true;
            this.textContent = '⏳ Checking...';

            fetch('/ai/moderate-event', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_id: id })
            })
            .then(r => r.json())
            .then(data => {
                let statusClass = data.status.toLowerCase();
                let icon = '✅';
                if (statusClass === 'warning') icon = '⚠️';
                if (statusClass === 'flagged') icon = '🚫';

                badge.className = `ai-mod-badge ${statusClass}`;
                badge.innerHTML = `${icon} ${data.status} <span style="font-weight:400;opacity:0.8;margin-left:4px" title="${data.reason}">(Hover for reason)</span>`;
                badge.title = data.reason;
                badge.style.display = 'inline-flex';

                if (statusClass === 'flagged') {
                    this.closest('tr').style.backgroundColor = 'rgba(239, 68, 68, 0.05)';
                }
                
                this.style.display = 'none'; // hide button after check
            })
            .catch(() => {
                this.disabled = false;
                this.textContent = '🤖 AI Review';
            });
        });
    });

});
