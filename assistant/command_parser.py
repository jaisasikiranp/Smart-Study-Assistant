import re

class IntentMapper:
    @staticmethod
    def parse_intent(text):
        t = text.lower().strip()
        # Clean up common wake words and pleasantries if they lingered in the text
        WAKE_WORDS = ["alexa", "hey alexa", "hi alexa", "uh-lexa", "a-lexa", "alexaah", 
                      "alaxa", "aleksa", "alexo", "alessa", "alisha", "alexa sir", "a lexa", 
                      "lexa", "hey lexa", "hey", "hi", "please"]
        for w in WAKE_WORDS:
            # Use regex to replace exact word matches only to avoid partial word issues
            t = re.sub(rf"\b{re.escape(w)}\b", "", t).strip()

        if not t:
            return "unknown", None

        # Global Cancel
        if any(w in t for w in ["cancel", "stop", "nevermind", "forget it", "quit"]):
            return "cancel", None

        # Mapping Layer for Misheard Words / Accents
        MAP_DASHBOARD = ["dashboard", "dash board", "dashbored", "dashport", "dashboad", "home", "main"]
        MAP_CALENDAR = ["calendar", "calender", "calandar", "calender page", "schedule", "events", "agenda"]
        MAP_TASK = ["task", "tasks", "ask", "asks", "tusk", "tosk", "taks", "todo", "goal", "assignment"]
        MAP_NOTE = ["note", "notes", "not", "node", "noat", "memo", "thought", "journal"]
        MAP_RESOURCES = ["resources", "resorses", "resourses", "resource", "link", "url", "reference"]
        MAP_COURSE = ["course", "corse", "curse", "courses page", "courses", "class", "manager", "subjects"]
        
        MAP_TODAY_SCHEDULE = ["today schedule", "today's task", "today task", "today shedule", "todays skedule", "my agenda", "my schedule", "on the agenda"]
        MAP_UPCOMING = ["deadlines", "up coming deadlines", "upcoming dedlines", "dead lines", "upcoming", "deadline", "due"]
        MAP_PENDING = ["pending task", "incomplete tasks", "pending tusks", "pending task", "pedding tasks"]

        # 1. List / Read Data (Priority for specific queries)
        if any(w in t for w in ["show", "list", "read", "display", "what are", "what is", "what's", "tell me"]) or \
           any(w in t for w in MAP_TODAY_SCHEDULE):
            
            if any(w in t for w in MAP_TASK):
                if any(w in t for w in MAP_TODAY_SCHEDULE + ["today", "schedule", "agenda"]): return "today_schedule", None
                if any(w in t for w in MAP_UPCOMING): return "upcoming_tasks", None
                return "list_tasks", None
            
            if any(w in t for w in MAP_PENDING): return "list_tasks", None
            if any(w in t for w in MAP_TODAY_SCHEDULE + ["today", "schedule", "agenda"]): return "today_schedule", None
            if any(w in t for w in MAP_UPCOMING): return "upcoming_tasks", None
            if any(w in t for w in MAP_NOTE): return "list_notes", None

        # 2. Navigation
        pages = {
            "dashboard": MAP_DASHBOARD,
            "tasks": MAP_TASK + ["todo list", "to do", "notes list"],
            "notes": MAP_NOTE + ["journal"],
            "calendar": MAP_CALENDAR,
            "courses": MAP_COURSE,
            "resources": MAP_RESOURCES
        }
        nav_verbs = ["open", "go to", "show", "view", "display", "navigate to", "bring up", "switch to"]
        for page, keywords in pages.items():
            if any(verb in t for verb in nav_verbs):
                if any(k in t for k in keywords):
                    return "nav", page
        
        # 3. Add Task
        add_task_patterns = [
            r"(add|create|new|set|post|remind me to|put in|make|odd|at)\s+(a\s+)?(task|todo|to do|goal|assignment|tusk|ask|asks|tosk|taks)\s*(called|named|titled|to)?\s*(.*)",
            r"(remind me to)\s+(.*)"
        ]
        for p in add_task_patterns:
            m = re.search(p, t)
            if m:
                groups = m.groups()
                title = groups[-1].strip() if groups else ""
                return "add_task", title if title else None

        # 4. Complete Task
        complete_task_patterns = [
            r"(complete|finish|mark|done|check off|tick|done with)\s*(the|a)?\s*(task|todo|goal|assignment)?\s*(called|named|titled|as)?\s*(.*)",
            r"(mark)\s+(.*)\s+(as done|as completed|finished)"
        ]
        for p in complete_task_patterns:
            m = re.search(p, t)
            if m:
                groups = m.groups()
                title = groups[-1].strip() if groups else ""
                title = re.sub(r"\s+(as done|as completed|finished)$", "", title)
                if title: return "complete_task", title

        # Add Note
        add_note_patterns = [
            r"(add|create|new|take|write|save|start)\s+(a\s+)?(note|memo|thought|journal entry|not|node|noat|notes)\s*(called|named|titled|about)?\s*(.*)",
            r"(take a note about)\s+(.*)"
        ]
        for p in add_note_patterns:
            m = re.search(p, t)
            if m:
                groups = m.groups()
                title = groups[-1].strip() if groups else ""
                return "add_note", title if title else None

        # Add Resource
        add_res_patterns = [
            r"(add|create|new|save|put|make)\s+(a\s+)?(resource|link|url|bookmark|resources|resorses|resourses)\s*(called|named|titled)?\s*(.*)"
        ]
        for p in add_res_patterns:
            m = re.search(p, t)
            if m:
                groups = m.groups()
                title = groups[-1].strip() if groups else ""
                return "add_resource", title if title else None

        # Help
        if any(w in t for w in ["help", "what can you do", "commands", "how does this work"]):
            return "help", None

        return "unknown", None
