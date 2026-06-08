/**
 * EventEase — Creator Dashboard JS
 */

const CHART_COLORS = {
    primary: '#6C63FF',
    accent: '#FF6584',
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444',
    info: '#3B82F6'
};

document.addEventListener('DOMContentLoaded', () => {
    // Progress Bar Animation
    setTimeout(() => {
        document.querySelectorAll('.progress-fill').forEach(bar => {
            const w = bar.dataset.width || 0;
            bar.style.width = w + '%';
        });
    }, 300);

    // Chart.js Default Themes
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    Chart.defaults.color = isDark ? '#9CA3AF' : '#6B7280';
    Chart.defaults.borderColor = isDark ? '#2A2D45' : '#E5E7EB';
    Chart.defaults.font.family = "'DM Sans', sans-serif";

    if (window.CREATOR_CHART_DATA) {
        initCreatorCharts(window.CREATOR_CHART_DATA);
    }
});

function initCreatorCharts(data) {
    // 1. Revenue per Event (Bar)
    const ctxRev = document.getElementById('creatorRevChart');
    if (ctxRev && data.revenue_by_event) {
        new Chart(ctxRev, {
            type: 'bar',
            data: {
                labels: data.revenue_by_event.labels,
                datasets: [{
                    label: 'Revenue (₹)',
                    data: data.revenue_by_event.data,
                    backgroundColor: CHART_COLORS.primary,
                    borderRadius: 4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    // 2. Daily Registrations (Line)
    const ctxReg = document.getElementById('creatorRegChart');
    if (ctxReg && data.registration_trend) {
        new Chart(ctxReg, {
            type: 'line',
            data: {
                labels: data.registration_trend.labels,
                datasets: [{
                    label: 'Registrations',
                    data: data.registration_trend.data,
                    borderColor: CHART_COLORS.accent,
                    backgroundColor: CHART_COLORS.accent + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
        });
    }
}
