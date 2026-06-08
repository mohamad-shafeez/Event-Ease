/**
 * EventEase — Admin Dashboard JS
 * Chart.js rendering and live data refresh
 */

// Shared color palette matching our CSS variables
const CHART_COLORS = {
    primary: '#6C63FF',
    accent: '#FF6584',
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444',
    info: '#3B82F6',
    purple: '#A855F7',
    teal: '#06B6D4',
    orange: '#F97316',
    pink: '#EC4899'
};
const COLOR_ARRAY = Object.values(CHART_COLORS);

document.addEventListener('DOMContentLoaded', () => {
    // Determine which page we are on
    const isDashboard = document.getElementById('revChart') !== null;
    const isAnalytics = document.getElementById('growthChart') !== null;
    
    // Set Chart.js defaults for dark mode compatibility (uses CSS vars if possible, but fallback to gray)
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    Chart.defaults.color = isDark ? '#9CA3AF' : '#6B7280';
    Chart.defaults.borderColor = isDark ? '#2A2D45' : '#E5E7EB';
    Chart.defaults.font.family = "'DM Sans', sans-serif";

    if (isDashboard && window.CHART_DATA) {
        initAdminDashboardCharts(window.CHART_DATA);
        startLiveRefresh();
    }

    if (isAnalytics && window.ANALYTICS_DATA) {
        initDeepAnalyticsCharts(window.ANALYTICS_DATA);
        
        // Year selector AJAX
        const yearSel = document.getElementById('year-selector');
        if (yearSel) {
            yearSel.addEventListener('change', () => {
                window.location.href = '?year=' + yearSel.value;
            });
        }
    }
});

let revChartInst, regChartInst, typeChartInst, revTypeChartInst;

function initAdminDashboardCharts(data) {
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

    // 1. Monthly Revenue (Line)
    const ctxRev = document.getElementById('revChart');
    if (ctxRev) {
        revChartInst = new Chart(ctxRev, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Revenue (₹)',
                    data: data.revenue_monthly,
                    borderColor: CHART_COLORS.primary,
                    backgroundColor: CHART_COLORS.primary + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    // 2. Monthly Registrations (Bar)
    const ctxReg = document.getElementById('regChart');
    if (ctxReg) {
        regChartInst = new Chart(ctxReg, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [{
                    label: 'Registrations',
                    data: data.regs_monthly,
                    backgroundColor: CHART_COLORS.accent,
                    borderRadius: 4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    // 3. Events by Type (Doughnut)
    const ctxType = document.getElementById('typeChart');
    if (ctxType) {
        typeChartInst = new Chart(ctxType, {
            type: 'doughnut',
            data: {
                labels: data.events_type.labels,
                datasets: [{
                    data: data.events_type.data,
                    backgroundColor: COLOR_ARRAY,
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { boxWidth: 12 } } }, cutout: '70%' }
        });
    }

    // 4. Revenue by Event Type (Horizontal Bar)
    const ctxRevType = document.getElementById('revTypeChart');
    if (ctxRevType) {
        revTypeChartInst = new Chart(ctxRevType, {
            type: 'bar',
            data: {
                labels: data.revenue_type.labels,
                datasets: [{
                    label: 'Revenue',
                    data: data.revenue_type.data,
                    backgroundColor: CHART_COLORS.success,
                    borderRadius: 4
                }]
            },
            options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }
}

function startLiveRefresh() {
    setInterval(() => {
        fetch('/admin/api/stats')
            .then(res => res.json())
            .then(stats => {
                const map = {
                    'kpi-users': stats.total_users,
                    'kpi-creators': stats.total_creators,
                    'kpi-events': stats.total_events,
                    'kpi-regs': stats.total_registrations,
                    'kpi-rev': '₹' + Math.round(stats.total_revenue),
                    'kpi-today': stats.events_today
                };
                for (let id in map) {
                    const el = document.getElementById(id);
                    if (el && el.innerText !== String(map[id])) {
                        el.innerText = map[id];
                        // Flash green effect
                        el.style.color = CHART_COLORS.success;
                        setTimeout(() => { el.style.color = ''; }, 1000);
                    }
                }
            })
            .catch(err => console.error("Live refresh failed:", err));
    }, 60000); // 60 seconds
}


function initDeepAnalyticsCharts(data) {
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

    // 1. User Growth (Line)
    const ctxGrowth = document.getElementById('growthChart');
    if (ctxGrowth) {
        new Chart(ctxGrowth, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'New Users',
                    data: data.user_growth,
                    borderColor: CHART_COLORS.info,
                    backgroundColor: CHART_COLORS.info + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    // 2. City Heatmap
    const ctxCity = document.getElementById('cityChart');
    if (ctxCity) {
        new Chart(ctxCity, {
            type: 'bar',
            data: {
                labels: data.city_heatmap.labels,
                datasets: [{
                    label: 'Events',
                    data: data.city_heatmap.data,
                    backgroundColor: CHART_COLORS.purple,
                    borderRadius: 4
                }]
            },
            options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    // 3. Payment Methods
    const ctxPay = document.getElementById('paymentChart');
    if (ctxPay) {
        new Chart(ctxPay, {
            type: 'pie',
            data: {
                labels: data.payment_methods.labels,
                datasets: [{
                    data: data.payment_methods.data,
                    backgroundColor: [CHART_COLORS.primary, CHART_COLORS.accent, CHART_COLORS.warning, CHART_COLORS.success],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
        });
    }

    // 4. Event Status
    const ctxStat = document.getElementById('statusChart');
    if (ctxStat) {
        new Chart(ctxStat, {
            type: 'doughnut',
            data: {
                labels: data.event_status.labels,
                datasets: [{
                    data: data.event_status.data,
                    backgroundColor: [CHART_COLORS.success, CHART_COLORS.info, CHART_COLORS.danger, CHART_COLORS.purple],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, cutout: '60%' }
        });
    }
}
