const taskForm = document.getElementById('taskForm');
const tasksUl = document.getElementById('tasks');
let tasks = JSON.parse(localStorage.getItem('tasks')) || [];
renderTasks();
taskForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const title = document.getElementById('taskTitle').value.trim();
    const desc = document.getElementById('taskDesc').value.trim();
    const priority = document.getElementById('taskPriority').value;
    if (!title) {
        alert("Task title is required!");
        return;
    }
    const task = {
        id: Date.now(),
        title,
        desc,
        priority,
        completed: false
    };
    tasks.push(task);
    saveAndRender();
    taskForm.reset();
});
function saveTasks() {
    localStorage.setItem('tasks', JSON.stringify(tasks));
}
function renderTasks() {
    tasksUl.innerHTML = '';
    tasks.forEach(task => {
        const li = document.createElement('li');
        li.className = task.completed ? 'completed' : '';
        li.innerHTML = `
            <div class="task-info">
                <span class="task-title">${task.title}</span>
                <span class="task-desc">${task.desc}</span>
            </div>
            <div style="display:flex;align-items:center;">
                <span class="task-priority ${task.priority.toLowerCase()}">${task.priority}</span>
                <div class="task-actions">
                    <button class="complete-btn">${task.completed ? 'Undo' : 'Complete'}</button>
                    <button class="delete-btn">Delete</button>
                </div>
            </div>
        `;
        li.querySelector('.complete-btn').addEventListener('click', () => {
            task.completed = !task.completed;
            saveAndRender();
        });
        li.querySelector('.delete-btn').addEventListener('click', () => {
            tasks = tasks.filter(t => t.id !== task.id);
            saveAndRender();
        });

        tasksUl.appendChild(li);
    });
}
function saveAndRender() {
    saveTasks();
    renderTasks();
}
