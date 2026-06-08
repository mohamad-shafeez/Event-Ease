/**
 * EventEase — Tickets JS
 * Form logic, payment simulation, and attendee table expands.
 */
document.addEventListener('DOMContentLoaded', () => {

    // ── Payment Tabs ─────────────────────────
    const payTabs = document.querySelectorAll('.pay-tab');
    const payPanels = document.querySelectorAll('.pay-panel');
    const methodInput = document.getElementById('payment-method-input');

    if (payTabs.length > 0) {
        payTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                payTabs.forEach(t => t.classList.remove('active'));
                payPanels.forEach(p => p.classList.remove('active'));
                
                tab.classList.add('active');
                const target = document.getElementById(tab.dataset.target);
                if (target) target.classList.add('active');
                
                if (methodInput) {
                    methodInput.value = tab.dataset.method;
                }
            });
        });
    }

    // ── Payment Auto-format ──────────────────
    const cardInput = document.getElementById('card_number');
    if (cardInput) {
        cardInput.addEventListener('input', function (e) {
            let v = this.value.replace(/\D/g, '').substring(0, 16);
            let formatted = v.match(/.{1,4}/g);
            this.value = formatted ? formatted.join(' ') : v;
        });
    }

    const expInput = document.getElementById('card_expiry');
    if (expInput) {
        expInput.addEventListener('input', function (e) {
            let v = this.value.replace(/\D/g, '').substring(0, 4);
            if (v.length > 2) {
                this.value = v.substring(0, 2) + '/' + v.substring(2, 4);
            } else {
                this.value = v;
            }
        });
    }

    // ── Payment Spinner ──────────────────────
    const payForm = document.getElementById('payment-form');
    if (payForm) {
        payForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const btn = document.getElementById('pay-btn');
            if (btn) btn.classList.add('btn-loading');
            
            // Simulate 1.5s delay
            setTimeout(() => {
                this.submit();
            }, 1500);
        });
    }

    // ── Dynamic Totals (Register Form) ───────
    const qtyInput = document.getElementById('qty');
    const totalSpan = document.getElementById('live-total');
    if (qtyInput && totalSpan) {
        const price = parseFloat(totalSpan.dataset.price || 0);
        qtyInput.addEventListener('input', () => {
            let q = parseInt(qtyInput.value || 1);
            if (q < 1) q = 1;
            if (q > 5) q = 5;
            totalSpan.textContent = '₹' + (q * price).toFixed(0);
        });
    }

    // ── My Tickets Tabs ──────────────────────
    const tTabs = document.querySelectorAll('.tickets-tabs .tab');
    if (tTabs.length > 0) {
        tTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                document.querySelectorAll('.tickets-view').forEach(v => v.style.display = 'none');
                document.getElementById(tab.dataset.target).style.display = 'block';
            });
        });
    }

    // ── Attendee Row Expand ──────────────────
    const expandBtns = document.querySelectorAll('.attendee-expand');
    expandBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const targetRow = document.getElementById(targetId);
            if (!targetRow) return;

            if (targetRow.classList.contains('open')) {
                targetRow.classList.remove('open');
                this.textContent = '+';
            } else {
                targetRow.classList.add('open');
                this.textContent = '−';
            }
        });
    });

});
