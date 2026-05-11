document.addEventListener('DOMContentLoaded', () => {
    let currentMonth = new Date().getMonth();
    let currentYear = new Date().getFullYear();
    let selectedDate = null;
    let backendTasks = [];

    const calendarGrid = document.getElementById('calendarGrid');
    const monthDisplay = document.getElementById('monthDisplay');
    const dayPanel = document.getElementById('dayPanel');
    const eventList = document.getElementById('eventList');
    const addEventForm = document.getElementById('addEventForm');

    // 1. DATA FETCHING
    const getEvents = () => JSON.parse(localStorage.getItem('studyEvents')) || {};
    const saveEvents = (data) => localStorage.setItem('studyEvents', JSON.stringify(data));

    const fetchBackendTasks = async () => {
        try {
            const res = await fetch('/api/calendar_data');
            backendTasks = await res.json();
            renderCalendar(currentMonth, currentYear);
        } catch (err) {
            console.error("Failed to fetch calendar tasks", err);
        }
    };

    // 2. HELPER: RENDER TASKS INSIDE CELL
    const renderTasksInCell = (tasks) => {
        if (!tasks || tasks.length === 0) return '';
        
        const maxVisible = 2;
        const visibleTasks = tasks.slice(0, maxVisible);
        const extraCount = tasks.length - maxVisible;

        let html = visibleTasks.map(t => `
            <div class="task-chip ${t.status === 'completed' ? 'completed' : ''}" title="${t.title}">
                Due: ${t.title}
            </div>
        `).join('');

        if (extraCount > 0) {
            html += `<div class="task-more">+${extraCount} more...</div>`;
        }

        return html;
    };

    // 3. RENDER MAIN CALENDAR GRID
    const renderCalendar = (month, year) => {
        calendarGrid.innerHTML = '';
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const today = new Date();

        monthDisplay.innerText = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(new Date(year, month));

        const events = getEvents();

        // Empty cells for alignment
        for (let i = 0; i < firstDay; i++) {
            const emptyCell = document.createElement('div');
            emptyCell.classList.add('day-cell', 'other-month');
            calendarGrid.appendChild(emptyCell);
        }

        // Generate Days
        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayCell = document.createElement('div');
            dayCell.classList.add('day-cell');

            const dayTasks = backendTasks.filter(t => t.deadline === dateStr);
            const isToday = day === today.getDate() && month === today.getMonth() && year === today.getFullYear();

            // Status Classes
            if (dayTasks.length > 0) {
                dayCell.classList.add('day-with-task');
                const isOverdue = dayTasks.some(t => t.status === 'pending' && t.color === '#ef4444');
                if (isOverdue) dayCell.classList.add('task-overdue');
            }
            if (isToday) dayCell.classList.add('current-day');

            // Cell Structure: [Circle with Number] + [Task Labels]
            dayCell.innerHTML = `
                <div class="circle-number">${day}</div>
                <div style="width: 100%; overflow: hidden;">
                    ${renderTasksInCell(dayTasks)}
                </div>
            `;

            dayCell.onclick = () => openDayPanel(dateStr);
            calendarGrid.appendChild(dayCell);
        }
    };

    // 4. DAY PANEL / MODAL LOGIC
    window.openDayPanel = (dateStr) => {
        selectedDate = dateStr;
        document.getElementById('selectedDateHeader').innerText = new Date(dateStr).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
        dayPanel.style.display = 'block';
        renderDayEvents();
    };

    window.closeDayPanel = () => {
        dayPanel.style.display = 'none';
        selectedDate = null;
    };

    const renderDayEvents = () => {
        const events = getEvents();
        const customEvents = events[selectedDate] || [];
        const dayTasks = backendTasks.filter(t => t.deadline === selectedDate);
        
        if (customEvents.length === 0 && dayTasks.length === 0) {
            eventList.innerHTML = '<div class="empty-state">No tasks or sessions for today.</div>';
            return;
        }

        let html = '';
        if (dayTasks.length > 0) {
            html += '<h4 style="margin-bottom: 0.5rem; color: #64748b; font-size: 0.75rem; text-transform: uppercase;">📅 Academic Deadlines</h4>';
            html += dayTasks.map(t => `
                <div class="day-event-card" style="border-left: 4px solid ${t.color}">
                    <div style="display: flex; justify-content: space-between;">
                        <h4>${t.title}</h4>
                        <span style="font-size: 0.7rem; color: ${t.color}; font-weight: 800;">${t.status.toUpperCase()}</span>
                    </div>
                    <p style="font-size: 0.8rem; color: #64748b; margin: 4px 0;">${t.description || ''}</p>
                    <div style="display: flex; gap: 0.5rem; margin-top: 10px;">
                        ${t.status === 'pending' ? `<button onclick="completeTaskFromCalendar(${t.id})" class="action-btn-sm" style="background: #10b981; color: white;">Complete</button>` : ''}
                        <button onclick="deleteTaskFromCalendar(${t.id})" class="action-btn-sm" style="background: #ef4444; color: white;">Delete</button>
                    </div>
                </div>
            `).join('');
        }

        if (customEvents.length > 0) {
            html += '<h4 style="margin-top: 1.5rem; margin-bottom: 0.5rem; color: #64748b; font-size: 0.75rem; text-transform: uppercase;">🕒 Personal Schedule</h4>';
            html += customEvents.map((ev, index) => `
                <div class="day-event-card">
                    <h4>${ev.title}</h4>
                    <span class="day-event-time">🕒 ${ev.start} - ${ev.end}</span>
                    <button onclick="deleteEvent(${index})" style="background: none; border: none; color: #ef4444; float: right; cursor: pointer; font-size: 0.75rem;">Delete</button>
                </div>
            `).join('');
        }
        eventList.innerHTML = html;
    };

    // 5. EVENT HANDLERS
    window.completeTaskFromCalendar = async (id) => {
        const res = await fetch(`/tasks/complete/${id}`, { method: 'POST' });
        if (res.ok) fetchBackendTasks();
    };

    window.deleteTaskFromCalendar = async (id) => {
        if (!confirm("Delete this academic record?")) return;
        const res = await fetch(`/tasks/delete/${id}`, { method: 'POST' });
        if (res.ok) fetchBackendTasks();
    };

    addEventForm.onsubmit = (e) => {
        e.preventDefault();
        const title = document.getElementById('eventTitle').value;
        const start = document.getElementById('startTime').value;
        const end = document.getElementById('endTime').value;
        const events = getEvents();
        if (!events[selectedDate]) events[selectedDate] = [];
        events[selectedDate].push({ title, start, end });
        saveEvents(events);
        addEventForm.reset();
        renderDayEvents();
        renderCalendar(currentMonth, currentYear);
    };

    window.deleteEvent = (index) => {
        const events = getEvents();
        events[selectedDate].splice(index, 1);
        saveEvents(events);
        renderDayEvents();
        renderCalendar(currentMonth, currentYear);
    };

    // 6. NAVIGATION
    document.getElementById('prevMonth').onclick = () => {
        currentMonth--;
        if (currentMonth < 0) { currentMonth = 11; currentYear--; }
        renderCalendar(currentMonth, currentYear);
    };

    document.getElementById('nextMonth').onclick = () => {
        currentMonth++;
        if (currentMonth > 11) { currentMonth = 0; currentYear++; }
        renderCalendar(currentMonth, currentYear);
    };

    fetchBackendTasks();
});
