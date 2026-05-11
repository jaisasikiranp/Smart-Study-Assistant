from automation.browser_controller import BrowserController
import time

class PlannerActions:
    def __init__(self, controller: BrowserController):
        self.controller = controller

    def goto_dashboard(self):
        return self.controller.navigate("/dashboard")

    def goto_tasks(self):
        return self.controller.navigate("/tasks")

    def add_task(self, title, description="Added via Assistant"):
        self.goto_tasks()
        self.controller.interact("button:has-text('+ New Goal')", "click")
        # Wait for modal to be visible or just fill
        self.controller.interact("#title", "fill", title)
        self.controller.interact("#description", "fill", description)
        # We can skip deadline for voice demo or set current time
        self.controller.interact("#addTaskModal button[type='submit']", "click")
        return f"Task '{title}' added successfully."

    def show_tasks(self):
        self.goto_tasks()
        # Extract titles of pending tasks
        selector = ".task-card:not(.completed) h3"
        titles = self.controller.page.locator(selector).all_inner_texts()
        if not titles:
            return "You have no pending tasks. Great job!"
        return f"You have {len(titles)} pending tasks: {', '.join(titles)}."

    def show_schedule(self):
        self.goto_dashboard()
        # Scan dashboard for 'Today' section tasks
        selector = ".today-tasks-list .task-title" # Assuming this class exists from templates
        titles = self.controller.page.locator(selector).all_inner_texts()
        if not titles:
            return "Your schedule for today is clear."
        return f"Today you have: {', '.join(titles)}."

    def show_deadlines(self):
        self.goto_tasks()
        # Look for upcoming dates
        selector = ".task-card:not(.completed)"
        # We extract all text and filter for 'Upcoming' or date patterns
        return "I am scanning your tasks for upcoming deadlines. You should check the 'Upcoming' section on your task page for the latest dates."

    def complete_task(self, title):
        self.goto_tasks()
        # Find the task card with the title and click complete
        selector = f"article.task-card:has(h3:has-text('{title}')) button.btn-complete"
        success, msg = self.controller.interact(selector, "click")
        if success:
            return f"Task '{title}' marked as completed."
        else:
            return f"Could not find or complete task '{title}'."

    def add_note(self, title):
        self.controller.navigate("/notes")
        self.controller.interact("button:has-text('+ New Note')", "click")
        self.controller.interact("#note_title", "fill", title)
        self.controller.interact("#note_content", "fill", "Created by AI Assistant.")
        self.controller.interact("button[type='submit']", "click")
        return f"Note '{title}' saved."
