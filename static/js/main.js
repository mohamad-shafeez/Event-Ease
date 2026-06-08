/**
 * EventEase — Global JavaScript
 * Dark mode toggle, mobile nav, flash dismiss, navbar scroll
 */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initMobileNav();
    initFlashMessages();
    initNavbarScroll();
});

/* ── Dark Mode Toggle ───────────────────────── */
function initThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    const saved = localStorage.getItem('eventease-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');

    document.documentElement.setAttribute('data-theme', theme);
    updateToggleIcon(toggle, theme);

    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('eventease-theme', next);
        updateToggleIcon(toggle, next);
    });
}

function updateToggleIcon(btn, theme) {
    btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    btn.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
}

/* ── Mobile Nav Toggle ──────────────────────── */
function initMobileNav() {
    const toggle = document.getElementById('nav-toggle');
    const links = document.getElementById('nav-links');
    if (!toggle || !links) return;

    toggle.addEventListener('click', () => {
        links.classList.toggle('open');
        const isOpen = links.classList.contains('open');
        toggle.setAttribute('aria-expanded', isOpen);
    });

    // Close on link click
    links.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => links.classList.remove('open'));
    });
}

/* ── Flash Messages Auto-Dismiss ────────────── */
function initFlashMessages() {
    document.querySelectorAll('.flash').forEach(flash => {
        // Auto dismiss after 5s
        setTimeout(() => dismissFlash(flash), 5000);

        const closeBtn = flash.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => dismissFlash(flash));
        }
    });
}

function dismissFlash(el) {
    el.style.animation = 'flashOut .3s ease forwards';
    setTimeout(() => el.remove(), 300);
}

/* ── Navbar Scroll Effect ───────────────────── */
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    const onScroll = () => {
        navbar.classList.toggle('scrolled', window.scrollY > 10);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
}

/* ── Generic Form Submit Loading State ──────── */
document.addEventListener('submit', function(e) {
    if (e.target.tagName === 'FORM') {
        const submitBtn = e.target.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.classList.contains('no-loading')) {
            submitBtn.classList.add('btn-loading');
        }
    }
});

/* ── Notifications & Messages Polling ───────── */
function initPolling() {
    const msgBadge = document.getElementById('nav-msg-badge');
    const notifBadge = document.getElementById('nav-notif-badge');
    
    if (!msgBadge && !notifBadge) return; // Not logged in
    
    async function updateCounts() {
        try {
            // Unread messages
            if (msgBadge) {
                const resMsg = await fetch('/messages/unread-count');
                const dataMsg = await resMsg.json();
                if (dataMsg.count > 0) {
                    msgBadge.textContent = dataMsg.count;
                    msgBadge.style.display = 'block';
                } else {
                    msgBadge.style.display = 'none';
                }
            }
            
            // Unread notifications
            if (notifBadge) {
                const resNotif = await fetch('/notifications/unread-count');
                const dataNotif = await resNotif.json();
                if (dataNotif.count > 0) {
                    notifBadge.textContent = dataNotif.count;
                    notifBadge.style.display = 'block';
                } else {
                    notifBadge.style.display = 'none';
                }
            }
        } catch (err) {}
    }
    
    updateCounts();
    setInterval(updateCounts, 30000); // Poll every 30s
    
    // Notification Dropdown
    const notifBtn = document.getElementById('nav-notifications');
    const notifDropdown = document.getElementById('notif-dropdown');
    
    if (notifBtn && notifDropdown) {
        notifBtn.addEventListener('click', async (e) => {
            if (e.target.closest('.dropdown-menu')) return; // Clicked inside
            
            const isVisible = notifDropdown.style.display === 'block';
            if (isVisible) {
                notifDropdown.style.display = 'none';
            } else {
                notifDropdown.style.display = 'block';
                
                // Fetch notifications
                try {
                    const res = await fetch('/notifications/');
                    const data = await res.json();
                    
                    const list = document.getElementById('notif-list');
                    if (data.notifications && data.notifications.length > 0) {
                        list.innerHTML = data.notifications.map(n => `
                            <a href="${n.link || '#'}" style="text-decoration: none; color: inherit; display: block; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); transition: 0.2s;" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='rgba(255,255,255,0.02)'">
                                <div style="font-size: 0.9rem; margin-bottom: 4px;">${n.message}</div>
                                <div style="font-size: 0.75rem; color: var(--text-muted);">${n.date_str}</div>
                            </a>
                        `).join('');
                        
                        // Hide badge since we marked them as read
                        notifBadge.style.display = 'none';
                        notifBadge.textContent = '0';
                    } else {
                        list.innerHTML = '<div class="text-muted text-center" style="font-size: 0.9rem;">No new notifications</div>';
                    }
                } catch(err) {
                    console.error(err);
                }
            }
        });
        
        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!notifBtn.contains(e.target)) {
                notifDropdown.style.display = 'none';
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', initPolling);
