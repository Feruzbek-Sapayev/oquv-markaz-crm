document.addEventListener('DOMContentLoaded', () => {
    if (!window.attendanceConfig) {
        console.error('attendanceConfig not found!');
        return;
    }
    
    console.log('session_list.js loaded. Attaching listeners...');

    document.querySelectorAll('.attendance-cell[data-student]:not(.future-date)').forEach(cell => {
        cell.addEventListener('click', function() {
            if (window.attendanceConfig.isStudent) {
                console.log('Student cannot edit attendance');
                return;
            }
            
            const studentId = this.dataset.student;
            const date = this.dataset.date;
            const groupId = this.dataset.group;
            let status = this.dataset.status;

            console.log(`Click on cell: Student=${studentId}, Date=${date}, CurrentStatus=${status}`);

            const statuses = ['', 'present', 'absent'];
            let nextIndex = (statuses.indexOf(status) + 1) % statuses.length;
            const nextStatus = statuses[nextIndex];

            console.log(`Next status logic: ${status} -> ${nextStatus}`);

            // Optimistic UI update
            updateCellUI(this, nextStatus);
            this.dataset.status = nextStatus;
            
            updateRowPercentage(this.closest('tr'));

            fetch(window.attendanceConfig.updateUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.attendanceConfig.csrfToken
                },
                body: JSON.stringify({
                    student_id: studentId,
                    date: date,
                    status: nextStatus,
                    group_id: groupId
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Server response:', data);
                if (data.status !== 'success') {
                    alert(data.message || 'Xatolik yuz berdi!');
                    location.reload(); 
                }
            })
            .catch(err => {
                console.error('Fetch error:', err);
                alert('Serverga ulanishda xatolik yuz berdi. Iltimos qaytadan urinib ko\'ring.');
                location.reload();
            });
        });
    });
});

function updateCellUI(cell, status) {
    const iconDiv = cell.querySelector('.att-status-circle');
    if (!iconDiv) return;
    iconDiv.className = 'att-status-circle';
    iconDiv.innerHTML = '';
    
    if (status === 'present') {
        iconDiv.classList.add('att-present');
        iconDiv.innerHTML = '<i class="fas fa-check"></i>';
    } else if (status === 'absent') {
        iconDiv.classList.add('att-absent');
        iconDiv.innerHTML = '<i class="fas fa-times"></i>';
    } else {
        iconDiv.classList.add('att-empty');
    }
}

function updateRowPercentage(row) {
    const cells = row.querySelectorAll('td[data-status]');
    const pctContainer = row.querySelector('.pct-col');
    if (!pctContainer) return;

    let presentCount = 0;
    let absentCount = 0;
    let totalWithStatus = 0;
    
    cells.forEach(c => {
        const s = c.dataset.status;
        if (s === 'present') {
            presentCount++;
            totalWithStatus++;
        } else if (s === 'absent') {
            absentCount++;
            totalWithStatus++;
        }
    });
    
    // Update the summary display
    const greenSpan = pctContainer.querySelector('span[style*="var(--att-green)"]');
    const redSpan = pctContainer.querySelector('span[style*="var(--att-red)"]');
    const pctValue = pctContainer.querySelector('div[style*="font-size:11px"]');

    if (greenSpan) greenSpan.textContent = presentCount;
    if (redSpan) redSpan.textContent = absentCount;
    
    if (pctValue) {
        const percentage = totalWithStatus > 0 ? Math.round((presentCount / totalWithStatus) * 100) : 0;
        pctValue.textContent = percentage + '%';
    }
}
