document.addEventListener('DOMContentLoaded', () => {
    // 1. REQUEST PERMISSION
    if ("Notification" in window) {
        if (Notification.permission !== "granted" && Notification.permission !== "denied") {
            Notification.requestPermission();
        }
    }

    // 2. DATA STORAGE FOR NOTIFIED IDS
    const getNotifiedTasks = () => JSON.parse(localStorage.getItem('notifiedTaskIDs')) || [];
    const saveNotifiedTask = (id) => {
        const notified = getNotifiedTasks();
        if (!notified.includes(id)) {
            notified.push(id);
            localStorage.setItem('notifiedTaskIDs', JSON.stringify(notified));
        }
    };

    // 3. REMINDER CHECK LOGIC
    const checkDeadlines = async () => {
        try {
            const res = await fetch('/api/calendar_data'); // Reusing existing task fetcher
            const tasks = await res.json();
            const now = new Date();
            const notifiedIDs = getNotifiedTasks();

            tasks.forEach(task => {
                if (task.status !== 'pending' || notifiedIDs.includes(task.id)) return;

                // Combine deadline & time (backend already returns deadline string)
                const deadlineDate = new Date(`${task.deadline}T${task.time}`);
                const diffMinutes = (deadlineDate - now) / (1000 * 60);

                // Trigger if due in exactly 30 mins (or between 25-30 if checked late)
                if (diffMinutes > 0 && diffMinutes <= 30) {
                    triggerNotification(task);
                    saveNotifiedTask(task.id);
                }
            });
        } catch (err) {
            console.error("Notification check failed", err);
        }
    };

    // 4. TRIGGER FUNCTION
    const triggerNotification = (task) => {
        if (Notification.permission === "granted") {
            new Notification("⏰ Study Reminder", {
                body: `Your task '${task.title}' is due in 30 minutes!`,
                icon: "/static/favicon.ico" // Placeholder for icon
            });
            console.log(`Notification sent for task: ${task.title}`);
        }
    };

    // 5. BACKGROUND LOOP (Every 1 minute)
    setInterval(checkDeadlines, 60000);
    
    // Initial check on load
    checkDeadlines();
});
