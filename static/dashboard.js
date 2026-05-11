/**
 * Smart Study Assistant - Reactive Dashboard (Precision API Sync)
 * Features: High-Priority Deadlines Hub, Event-Driven Task Sync, 2026 Accuray.
 */

const loadDashboardData = () => {
    console.log('Refreshing Dashboard Scholastic State...');
    
    // UI Elements Scan
    const todaySchedule = document.getElementById('todaySchedule');
    const pendingTasksList = document.getElementById('pendingTasksList');
    const upcomingDeadlines = document.getElementById('upcomingDeadlines');
    const pendingCountBadge = document.getElementById('pendingCount');

    // Early termination if not on Dashboard UI
    if (!todaySchedule || !pendingTasksList) return;

    // Helper to render scholastic task lists
    const renderTaskList = (container, tasks, emptyMsg, showDeadline = false) => {
        if (!container) return;
        if (!tasks || tasks.length === 0) {
            container.innerHTML = `<div class="empty-state" style="padding: 1rem; color: #64748b; font-style: italic;">${emptyMsg}</div>`;
            return;
        }
        
        container.innerHTML = `<ul style="list-style: none; padding:0; margin:0;">` + 
            tasks.map(t => `
            <li style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid #f1f5f9; animation: slideIn 0.3s ease forwards;">
                <span style="font-weight: 500; color: #1e293b;">• ${t.title}</span>
                <span style="font-size: 0.75rem; color: #64748b; background: #f8fafc; padding: 0.25rem 0.5rem; border-radius: 4px;">${showDeadline ? t.deadline : ''}</span>
            </li>`).join('') + `</ul>`;
    }

    // 1. Fetch Today's Tasks (Precision Engine)
    fetch('/api/tasks/today')
        .then(res => res.json())
        .then(data => {
            renderTaskList(todaySchedule, data, "You're all caught up for today!");
        })
        .catch(err => console.log("Today Schedule Fetch Error:", err));

    // 2. Fetch Pending Tasks (Inventory Sync)
    fetch('/api/tasks/pending')
        .then(res => res.json())
        .then(data => {
            renderTaskList(pendingTasksList, data, "All tasks completed! 🎉");
            if (pendingCountBadge) {
                pendingCountBadge.innerText = data.length;
            }
        })
        .catch(err => console.log("Pending Tasks Fetch Error:", err));

    // 3. Fetch Upcoming Deadlines (PRECISION ENDPOINT SYNC: /api/tasks/upcoming)
    fetch('/api/tasks/upcoming')
        .then(res => res.json())
        .then(data => {
            renderTaskList(upcomingDeadlines, data, "No deadlines approaching.", true);
        })
        .catch(err => console.log("Upcoming Deadlines Fetch Error:", err));
};

// INITIALIZATION HUB
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    // Refresh interval for live dashboard status (every 60s)
    setInterval(loadDashboardData, 60000); 
});

// CRITICAL FIX: Listen for Voice Assistant updates from this tab or others
window.addEventListener('taskUpdated', loadDashboardData);
window.addEventListener('storage', (event) => {
    if (event.key === 'voiceCommand') {
        // Delay slightly to allow DB write to finish
        setTimeout(loadDashboardData, 1000);
    }
});
