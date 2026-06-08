/**
 * EventEase — Browse Events JS
 * Search, filter, sort with AJAX, capacity bar animation
 */
document.addEventListener('DOMContentLoaded', () => {
    // Capacity bar animation
    document.querySelectorAll('.capacity-bar-fill').forEach(bar => {
        const w = bar.dataset.width || '0';
        setTimeout(() => { bar.style.width = w + '%'; }, 200);
    });

    // Filter form submit → update URL and reload
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', e => {
            e.preventDefault();
            applyFilters();
        });
        filterForm.addEventListener('reset', () => {
            setTimeout(() => { window.location.href = '/events'; }, 50);
        });
    }

    // Sort change
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', () => applyFilters());
    }

    // Search on enter
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => applyFilters(), 500);
        });
    }

    function applyFilters() {
        const params = new URLSearchParams();
        // Search
        const search = document.getElementById('search-input');
        if (search && search.value.trim()) params.set('search', search.value.trim());
        // Type checkboxes
        document.querySelectorAll('input[name="type"]:checked').forEach(cb => params.append('type', cb.value));
        // City
        const city = document.getElementById('filter-city');
        if (city && city.value.trim()) params.set('city', city.value.trim());
        // Date range
        const df = document.getElementById('filter-date-from');
        const dt = document.getElementById('filter-date-to');
        if (df && df.value) params.set('date_from', df.value);
        if (dt && dt.value) params.set('date_to', dt.value);
        // Price
        const price = document.querySelector('input[name="price"]:checked');
        if (price && price.value !== 'any') params.set('price', price.value);
        // Sort
        const sort = document.getElementById('sort-select');
        if (sort && sort.value) params.set('sort', sort.value);

        window.location.href = '/events?' + params.toString();
    }

    // Copy share link
    document.querySelectorAll('.share-copy').forEach(btn => {
        btn.addEventListener('click', () => {
            navigator.clipboard.writeText(window.location.href).then(() => {
                btn.textContent = 'Copied!';
                setTimeout(() => { btn.textContent = 'Copy Link'; }, 2000);
            });
        });
    });

    // Bookmarks
    document.querySelectorAll('.bookmark-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const eventId = btn.dataset.eventId;
            try {
                const res = await fetch(`/events/save/${eventId}`, { method: 'POST' });
                const data = await res.json();
                
                const icon = btn.querySelector('i');
                if (data.saved) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    btn.style.color = 'var(--primary)';
                } else {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    btn.style.color = btn.style.background.includes('0.2') ? 'white' : 'var(--text-light)';
                }
            } catch (err) {
                console.error("Failed to bookmark", err);
            }
        });
    });
});
