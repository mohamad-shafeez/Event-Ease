/**
 * EventEase — Create Event Wizard
 * 3-step form with dynamic type-specific fields
 */

const TYPE_FIELDS = {
    concert: [
        { key:'seating_type', label:'Seating Type', type:'select', options:['General Admission','Allocated Seating','VIP'], required:true },
        { key:'artist_name', label:'Artist / Band Name', type:'text', required:true },
        { key:'age_restriction', label:'Age Restriction (18+)?', type:'select', options:['No','Yes (18+)'] }
    ],
    tech_conference: [
        { key:'speaker_names', label:'Speaker Names', type:'textarea', placeholder:'One per line' },
        { key:'session_tracks', label:'Session Tracks', type:'text', placeholder:'e.g. AI, Web Dev, Cloud' },
        { key:'dress_code', label:'Dress Code', type:'select', options:['Casual','Business Casual','Formal'] }
    ],
    workshop: [
        { key:'skill_level', label:'Skill Level Required', type:'select', options:['Beginner','Intermediate','Advanced'], required:true },
        { key:'materials_provided', label:'Materials Provided?', type:'select', options:['Yes','No'] },
        { key:'max_batch_size', label:'Max Batch Size', type:'number' }
    ],
    sports: [
        { key:'sport_name', label:'Sport', type:'text', required:true },
        { key:'team_or_individual', label:'Format', type:'select', options:['Team','Individual'] },
        { key:'max_team_size', label:'Max Team Size', type:'number' },
        { key:'equipment_provided', label:'Equipment Provided?', type:'select', options:['Yes','No'] }
    ],
    wedding: [
        { key:'dress_code', label:'Dress Code', type:'text' },
        { key:'rsvp_deadline', label:'RSVP Deadline', type:'date' },
        { key:'meal_options', label:'Meal Options', type:'select', options:['Vegetarian','Non-Vegetarian','Both'] }
    ],
    exhibition: [
        { key:'industry', label:'Industry / Category', type:'text' },
        { key:'exhibitor_companies', label:'Exhibitor Companies', type:'textarea', placeholder:'One per line' },
        { key:'badge_required', label:'Entry Badge Required?', type:'select', options:['Yes','No'] }
    ],
    webinar: [
        { key:'platform', label:'Platform', type:'select', options:['Zoom','Google Meet','Microsoft Teams','Custom'], required:true },
        { key:'recording_available', label:'Recording Available?', type:'select', options:['Yes','No'] },
        { key:'certificate_provided', label:'Certificate Provided?', type:'select', options:['Yes','No'] }
    ],
    food_festival: [
        { key:'cuisines', label:'Cuisines Featured', type:'text', placeholder:'e.g. Italian, Indian, Mexican' },
        { key:'stalls_count', label:'Number of Stalls', type:'number' },
        { key:'alcohol_served', label:'Alcohol Served?', type:'select', options:['Yes','No'] }
    ],
    charity: [
        { key:'ngo_name', label:'NGO / Organization Name', type:'text', required:true },
        { key:'cause_category', label:'Cause Category', type:'select', options:['Education','Healthcare','Environment','Poverty','Animal Welfare','Other'] },
        { key:'donation_based', label:'Donation-Based Entry?', type:'select', options:['Yes','No'] },
        { key:'volunteer_slots', label:'Volunteer Slots', type:'number' }
    ],
    comedy: [
        { key:'show_name', label:'Show / Act Name', type:'text' },
        { key:'cast_names', label:'Cast / Performers', type:'textarea', placeholder:'One per line' },
        { key:'age_rating', label:'Age Rating', type:'select', options:['All Ages','13+','16+','18+'] },
        { key:'duration_minutes', label:'Duration (minutes)', type:'number' }
    ]
};

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('create-event-form') || document.getElementById('edit-event-form');
    if (!form) return;

    // Prevent past dates
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    const minDateTime = now.toISOString().slice(0, 16);
    const dateStart = document.getElementById('date_start');
    const dateEnd = document.getElementById('date_end');
    if (dateStart) dateStart.min = minDateTime;
    if (dateEnd) dateEnd.min = minDateTime;

    const panels = form.querySelectorAll('.wizard-panel');
    const steps = document.querySelectorAll('.wizard-step');
    let current = 0;

    // Step navigation
    form.addEventListener('click', e => {
        if (e.target.matches('[data-action="next"]')) { e.preventDefault(); goStep(current + 1); }
        if (e.target.matches('[data-action="back"]')) { e.preventDefault(); goStep(current - 1); }
    });

    function goStep(idx) {
        if (idx < 0 || idx >= panels.length) return;
        if (idx > current && !validateStep(current)) return;
        panels[current].classList.remove('active');
        steps[current].classList.remove('active');
        steps[current].classList.add('done');
        current = idx;
        panels[current].classList.add('active');
        steps[current].classList.add('active');
        steps[current].classList.remove('done');
        // Mark previous steps as done
        for (let i = 0; i < current; i++) { steps[i].classList.add('done'); steps[i].classList.remove('active'); }
        for (let i = current + 1; i < steps.length; i++) { steps[i].classList.remove('done', 'active'); }
    }

    function validateStep(idx) {
        const panel = panels[idx];
        const required = panel.querySelectorAll('[required]');
        let valid = true;
        required.forEach(input => {
            if (!input.value.trim()) {
                input.style.borderColor = 'var(--danger)';
                valid = false;
                input.addEventListener('input', () => { input.style.borderColor = ''; }, { once: true });
            }
        });
        if (!valid) {
            const first = panel.querySelector('[required]:invalid, [style*="danger"]');
            if (first) first.focus();
        }
        return valid;
    }

    // Dynamic type fields
    const typeSelect = document.getElementById('event-type');
    const container = document.getElementById('dynamic-fields');
    if (typeSelect && container) {
        typeSelect.addEventListener('change', () => renderFields(typeSelect.value));
        // Pre-render if editing
        if (typeSelect.value) renderFields(typeSelect.value);
    }

    function renderFields(type) {
        const fields = TYPE_FIELDS[type];
        if (!fields) { container.innerHTML = '<p class="text-muted">Select an event type to see specific fields.</p>'; return; }
        // Get existing values (for edit mode)
        const existing = window.EXISTING_DETAILS || {};
        container.innerHTML = fields.map(f => {
            const val = existing[f.key] || '';
            let input;
            if (f.type === 'select') {
                input = `<select class="form-input" name="detail_${f.key}" id="detail_${f.key}" ${f.required ? 'required' : ''}>
                    <option value="">Select...</option>
                    ${f.options.map(o => `<option value="${o}" ${val === o ? 'selected' : ''}>${o}</option>`).join('')}
                </select>`;
            } else if (f.type === 'textarea') {
                input = `<textarea class="form-input" name="detail_${f.key}" id="detail_${f.key}" placeholder="${f.placeholder || ''}" rows="3">${val}</textarea>`;
            } else {
                input = `<input class="form-input" type="${f.type}" name="detail_${f.key}" id="detail_${f.key}" value="${val}" placeholder="${f.placeholder || ''}" ${f.required ? 'required' : ''}>`;
            }
            return `<div class="form-group"><label class="form-label" for="detail_${f.key}">${f.label}</label>${input}</div>`;
        }).join('');
    }

    // Banner preview
    const bannerInput = document.getElementById('banner-input');
    const previewImg = document.getElementById('banner-preview-img');
    const previewText = document.getElementById('banner-preview-text');
    if (bannerInput && previewImg) {
        bannerInput.addEventListener('change', () => {
            const file = bannerInput.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = e => { previewImg.src = e.target.result; previewImg.style.display = 'block'; if (previewText) previewText.style.display = 'none'; };
                reader.readAsDataURL(file);
            }
        });
    }
});
