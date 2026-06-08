/**
 * EventEase — User Dashboard JS
 */

const CHART_COLORS = {
    primary: '#6C63FF',
    accent: '#FF6584',
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444',
    info: '#3B82F6',
    purple: '#A855F7',
    teal: '#06B6D4'
};
const COLOR_ARRAY = Object.values(CHART_COLORS);

document.addEventListener('DOMContentLoaded', () => {
    
    // Chart.js Defaults
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    Chart.defaults.color = isDark ? '#9CA3AF' : '#6B7280';
    Chart.defaults.borderColor = isDark ? '#2A2D45' : '#E5E7EB';
    Chart.defaults.font.family = "'DM Sans', sans-serif";

    if (window.USER_CHART_DATA) {
        initUserCharts(window.USER_CHART_DATA);
    }

    // Countdown Timers
    initCountdowns();
});

function initUserCharts(data) {
    // 1. Spending (Last 6 Months)
    const ctxSpend = document.getElementById('userSpendChart');
    if (ctxSpend && data.spending) {
        new Chart(ctxSpend, {
            type: 'bar',
            data: {
                labels: data.spending.labels,
                datasets: [{
                    label: 'Spent (₹)',
                    data: data.spending.data,
                    backgroundColor: CHART_COLORS.success,
                    borderRadius: 4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    // 2. Category History (Doughnut)
    const ctxHist = document.getElementById('userHistoryChart');
    if (ctxHist && data.history) {
        new Chart(ctxHist, {
            type: 'doughnut',
            data: {
                labels: data.history.labels,
                datasets: [{
                    data: data.history.data,
                    backgroundColor: COLOR_ARRAY,
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { boxWidth: 12 } } }, cutout: '70%' }
        });
    }
}

function initCountdowns() {
    const timers = document.querySelectorAll('.countdown-timer');
    if (timers.length === 0) return;

    function updateTimers() {
        const now = new Date().getTime();
        
        timers.forEach(timer => {
            const eventDate = new Date(timer.dataset.date).getTime();
            const distance = eventDate - now;

            if (distance < 0) {
                timer.innerHTML = "Event Started";
                return;
            }

            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));

            let display = '';
            if (days > 0) display += `${days}d `;
            display += `${hours}h ${minutes}m`;
            
            timer.innerHTML = display;
        });
    }

    updateTimers();
    setInterval(updateTimers, 60000); // Update every minute
}
