function highlight() {
    document.querySelectorAll('.student-row').forEach(row => {
        const selected = row.querySelector('input[type=radio]:checked');
        row.style.background = '';
        if (selected) {
            const v = selected.value;
            if (v === 'present') row.style.background = 'rgba(16,185,129,0.03)';
            else if (v === 'absent') row.style.background = 'rgba(239,68,68,0.03)';
        }
    });
}

document.querySelectorAll('.status-radio').forEach(radio => {
    radio.addEventListener('change', highlight);
});

function setAll(status) {
    document.querySelectorAll(`input[type=radio][value="${status}"]`).forEach(r => { 
        r.checked = true; 
    });
    highlight();
}

highlight();
