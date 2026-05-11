/**
 * Smart Study Assistant - AI Voice Intelligence (Precision Reporting Hub)
 * Features: High-Priority Deadlines Reporting, Pattern Resilient Hub, 2026 Sync.
 */

const VoiceAssistant = {
    recognition: null,
    isListening: false,
    currentAction: null,
    isProcessing: false,
    isSpeaking: false,
    listeningTimeout: null,
    tempTask: {},
    tempNote: {},
    tempResource: {},
    apiKey: "AIzaSyCDSdSY6Vq_uI-xfFm885Zluuae4IPoUDA",

    init() {
        this.setupRecognition();
        this.addHelpPill();
        this.askPermission();
        this.setupStorageListener();
        this.recoverPendingCommand();
        this.checkStickyActivation(); 
        
        this.showBubble("I can help you add tasks, notes, or read your schedule.", "system");
        console.log("Precision Reporting Hub Active.");
    },

    askPermission() {
        navigator.mediaDevices.getUserMedia({ audio: true }).catch(err => console.log("Mic access error."));
    },

    setupRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return;

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true; 
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = async (event) => {
            if (this.isSpeaking || this.isProcessing) return;
            const transcript = event.results[event.results.length - 1][0].transcript.trim().toLowerCase();
            console.log("User said:", transcript);
            if (!transcript) return;
            
            localStorage.setItem("voiceCommand", transcript);
            this.isProcessing = true;
            this.showBubble(transcript, 'user');
            await this.handleCommand(transcript);
            this.isProcessing = false;
        };

        this.recognition.onend = () => {
            if (this.isListening && !this.isSpeaking) {
                setTimeout(() => { if (this.isListening && !this.isSpeaking) this.startListening(true); }, 400); 
            }
        };
    },

    setupStorageListener() {
        window.addEventListener("storage", (event) => {
            if (event.key === "voiceCommand" && event.newValue) {
                this.handleCommand(event.newValue);
            }
        });
    },

    recoverPendingCommand() {
        const cmd = localStorage.getItem("voiceCommand");
        if (cmd) { this.handleCommand(cmd); localStorage.removeItem("voiceCommand"); }
    },

    checkStickyActivation() {
        const sticky = localStorage.getItem("assistantStickyMode");
        if (sticky === "active") {
            this.startListening(true);
            localStorage.removeItem("assistantStickyMode");
            this.resetTimeout(10000); 
        }
    },

    setSticky() {
        localStorage.setItem("assistantStickyMode", "active");
    },

    async handleCommand(text) {
        // Clean and prepare command
        const raw_c = this.cleanCommand(text).replace(/hey assistant|hey study|smart study|alexa/g, "").trim();
        const c = raw_c.toLowerCase();
        if (!c) return;

        if (!this.isListening) this.startListening(true);
        this.resetTimeout();

        // --- NAVIGATION HUB ---
        const navMatch = c.match(/(open|go to|show|view|navigate to|switch to|bring up) (dashboard|home|tasks|notes|resources|courses|calendar)/);
        if (navMatch || ["dashboard", "home", "tasks", "notes", "resources", "courses", "calendar"].includes(c)) {
            const page = (navMatch ? navMatch[2] : c).replace("home", "dashboard");
            const routes = {
                "dashboard": "/dashboard",
                "tasks": "/tasks",
                "notes": "/notes",
                "resources": "/resources",
                "courses": "/courses/manager",
                "calendar": "/calendar"
            };
            if (routes[page]) {
                this.speakOnce(`Opening ${page}.`);
                this.setSticky();
                window.location.href = routes[page];
                return;
            }
        }

        // --- REPORTING HUB (PRECISION SCAN) ---
        if (c.match(/(show|list|read|what are) (my )?(deadline|upcoming|due)/)) { 
            this.readUpcomingDeadlines(); return; 
        }
        if (c.match(/(show|list|read|what is) (my )?(today|agenda|schedule)/)) { 
            this.readTodaySchedule(); return; 
        }
        if (c.match(/(show|list|read|what are) (my )?(pending|tasks|todos)/)) { 
            this.readPendingTasks(); return; 
        }
        if (c.match(/(show|list|read) (my )?(notes|memos)/)) { 
            this.readNotes(); return; 
        }

        // --- MULTI-STEP CAPTURE HANDLING ---
        if (this.currentAction === "awaitingResourceDetails") {
            const urlHint = raw_c.replace(/\s/g, "");
            this.saveResource({ title: urlHint, url: urlHint });
            this.speakOnce("Resource saved.");
            this.currentAction = null; this.deactivate(); return;
        }
        if (this.currentAction === "awaitingTask") { 
            this.tempTask.title = raw_c; 
            this.speakOnce("When is the deadline?"); 
            this.currentAction = "awaitingDate"; return; 
        }
        if (this.currentAction === "awaitingDate") { 
            const d = this.parseDate(raw_c); 
            if (!d) { this.speakOnce("Please say the date again."); return; } 
            this.tempTask.deadlineDate = d; 
            this.speakOnce("What time?"); 
            this.currentAction = "awaitingTime"; return; 
        }
        if (this.currentAction === "awaitingTime") { 
            const t = this.parseTime(raw_c); 
            if (!t) { this.speakOnce("Please say the time again."); return; } 
            const finalDate = this.tempTask.deadlineDate; 
            finalDate.setHours(t.hours, t.minutes);
            this.saveReminder({ title: this.tempTask.title, deadline: finalDate });
            this.speakOnce(`Task added for ${this.formatDateTime(finalDate)}`);
            this.tempTask = {}; this.currentAction = null; this.deactivate(); return; 
        }
        if (this.currentAction === "awaitingNoteTitle") { 
            this.tempNote.title = raw_c; 
            this.speakOnce("What are the contents?"); 
            this.currentAction = "awaitingNoteContent"; return; 
        }
        if (this.currentAction === "awaitingNoteContent") { 
            this.tempNote.content = raw_c; 
            this.saveNote(this.tempNote); 
            this.speakOnce("Note saved."); 
            this.tempNote = {}; this.currentAction = null; this.deactivate(); return; 
        }

        // --- CREATION TRIGGERS ---
        const taskMatch = c.match(/(add|create|new|remind me to) (task|reminder|goal|todo)( called| named| to)? (.*)/);
        if (taskMatch) {
            this.tempTask.title = taskMatch[4];
            this.speakOnce(`Adding task ${this.tempTask.title}. When is it due?`);
            this.currentAction = "awaitingDate";
            return;
        }
        
        const noteMatch = c.match(/(add|create|new|take|write) (note|memo)( called| named)? (.*)/);
        if (noteMatch) {
            this.tempNote.title = noteMatch[4];
            this.speakOnce(`Note ${this.tempNote.title} started. What are the contents?`);
            this.currentAction = "awaitingNoteContent";
            return;
        }

        if (c.includes("add") || c.includes("create") || c.includes("new")) {
            if (c.includes("resource") || c.includes("link")) { this.speakOnce("What is the resource link?"); this.currentAction = "awaitingResourceDetails"; return; }
            if (c.includes("task") || c.includes("reminder") || c.includes("goal")) { this.speakOnce("What is the task about?"); this.currentAction = "awaitingTask"; return; }
            if (c.includes("note")) { this.speakOnce("What is the note title?"); this.currentAction = "awaitingNoteTitle"; return; }
        }

        // --- AI FALLBACK ---
        const intentData = await this.getAIIntent(c || raw_c);
        switch (intentData.intent) {
            case "addReminder": this.speakOnce("What is the task about?"); this.currentAction = "awaitingTask"; break;
            case "addNote": this.speakOnce("What note do you want to add?"); this.currentAction = "awaitingNoteTitle"; break;
            default: this.speakOnce("I can help with tasks, notes, or showing your schedule.");
        }
    },

    // (PRECISION 12-HOUR TIME PARSER)
    parseTime(text) {
        let cText = text.toLowerCase().replace(/\./g, ""); 
        let match = cText.match(/(\d{1,2})\s*:?\s*(\d{2})?\s*(am|pm|am|pm|p m|a m)?/);
        if (!match) return null;
        let hours = parseInt(match[1]);
        let minutes = match[2] ? parseInt(match[2]) : 0;
        let pmsuffix = match[3] || "";
        if ((pmsuffix.includes("p") || pmsuffix.includes("pm")) && hours < 12) hours += 12;
        if ((pmsuffix.includes("a") || pmsuffix.includes("am")) && hours === 12) hours = 0;
        console.log(`TIME PARSED: ${match[1]}:${minutes} ${pmsuffix} -> ${hours}:${minutes}`);
        return (hours >= 0 && hours < 24) ? { hours, minutes } : null;
    },

    parseDate(text) {
        const cText = text.toLowerCase().replace(/(\d+)(st|nd|rd|th)/g, "$1").trim();
        const anchorYear = 2026; const today = new Date(anchorYear, new Date().getMonth(), new Date().getDate());
        if (cText.includes("tomorrow")) { const d = new Date(today); d.setDate(today.getDate() + 1); return d; }
        if (cText.includes("today")) return new Date(today);
        const months = { january: 0, february: 1, march: 2, april: 3, may: 4, june: 5, july: 6, august: 7, september: 8, october: 9, november: 10, december: 11 };
        let words = cText.split(" "), day = null, month = null;
        words.forEach(word => { const val = parseInt(word); if (!isNaN(val) && val > 0 && val <= 31) day = val; if (months[word] !== undefined) month = months[word]; });
        if (day !== null && month !== null) { const d = new Date(anchorYear, month, day); if (d < today) d.setFullYear(anchorYear + 1); return d; }
        const fallback = new Date(cText); return (!isNaN(fallback.getTime())) ? fallback : null;
    },

    formatDateTime(date) { return date.toLocaleString("en-US", { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); },

    saveResource(resObj) {
        const formData = new FormData(); formData.append('title', resObj.title); formData.append('url', resObj.url);
        fetch('/resources/add', { method: 'POST', body: formData }).then(() => { if (window.location.pathname === '/resources') window.location.reload(); });
    },
    saveNote(noteObj) {
        const formData = new FormData(); formData.append('title', noteObj.title); formData.append('content', noteObj.content);
        fetch('/notes/add', { method: 'POST', body: formData }).then(() => { if (window.location.pathname === '/notes') window.location.reload(); });
    },
    saveReminder(details) {
        const formData = new FormData(); formData.append('title', details.title);
        const d = details.deadline; const formatted = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}T${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
        formData.append('deadline', formatted);
        fetch('/tasks/add', { method: 'POST', body: formData }).then(() => { if (window.location.pathname === '/tasks') window.location.reload(); });
    },

    async readTodaySchedule() {
        const r = await fetch('/api/tasks/today'); const tasks = await r.json();
        if (tasks.length === 0) this.speakOnce("You have no tasks today.");
        else { let msg = `You have ${tasks.length} tasks scheduled for today. `; tasks.forEach((t) => msg += `${t.title}. `); this.speakOnce(msg); }
    },
    async readPendingTasks() {
        const r = await fetch('/api/tasks/pending'); const tasks = await r.json();
        if (tasks.length === 0) this.speakOnce("You have no pending tasks.");
        else { let msg = `You have ${tasks.length} pending tasks. `; tasks.slice(0, 5).forEach((t, i) => msg += `Task ${i+1}: ${t.title}. `); this.speakOnce(msg); }
    },
    async readUpcomingDeadlines() {
        const r = await fetch('/api/tasks/upcoming'); const tasks = await r.json();
        if (!tasks || tasks.length === 0) this.speakOnce("You have no upcoming deadlines.");
        else { let msg = `You have ${tasks.length} upcoming deadlines. `; tasks.slice(0, 5).forEach((t) => msg += `${t.title} on ${t.deadline}. `); this.speakOnce(msg); }
    },
    async readNotes() {
        const r = await fetch('/api/notes/all'); const notes = await r.json();
        if (notes.length === 0) this.speakOnce("You have no notes.");
        else { let msg = `You have ${notes.length} notes. `; notes.slice(0, 5).forEach((n) => msg += `${n.title}. `); this.speakOnce(msg); }
    },

    cleanCommand(text) { return text.toLowerCase().replace(/[^\w\s]/gi, "").trim(); },

    speakOnce(text) {
        if (!text) return; this.isSpeaking = true; try { this.recognition.stop(); } catch(e) {}
        window.speechSynthesis.cancel(); const speech = new SpeechSynthesisUtterance(text);
        speech.lang = "en-US"; speech.onstart = () => this.showBubble(text, 'system');
        speech.onend = () => { 
            this.isSpeaking = false; 
            setTimeout(() => { if (this.isListening && !this.isSpeaking) this.startListening(true); }, 500); 
        };
        window.speechSynthesis.speak(speech);
    },

    toggle() { if (this.isListening) this.deactivate(); else this.startListening(); },

    startListening(silent = false) {
        this.isListening = true;
        document.getElementById('voiceBtn')?.classList.add('listening');
        document.getElementById('voiceBubbleContainer')?.classList.add('visible');
        if (!silent) this.speakOnce("Listening...");
        try { this.recognition.start(); } catch (e) {}
        this.resetTimeout(); 
    },

    deactivate() { 
        this.isListening = false; 
        if (this.listeningTimeout) clearTimeout(this.listeningTimeout);
        document.getElementById('voiceBtn')?.classList.remove('listening'); 
        document.getElementById('voiceBubbleContainer')?.classList.remove('visible');
        this.currentAction = null; 
        try { this.recognition.stop(); } catch(e) {}
        window.speechSynthesis.cancel(); 
    },

    resetTimeout(customTime = 30000) { 
        if (this.listeningTimeout) clearTimeout(this.listeningTimeout); 
        this.listeningTimeout = setTimeout(() => this.deactivate(), customTime); 
    },

    showBubble(text, type) {
        const container = document.getElementById('voiceBubbleContainer'); if (!container) return;
        const bubble = document.createElement('div'); bubble.className = `chat-bubble bubble-${type}`; bubble.textContent = text;
        container.appendChild(bubble); container.scrollTop = container.scrollHeight;
    },

    addHelpPill() {
        if (document.getElementById('voiceBtn')) return;
        const html = `
            <div id="voiceBubbleContainer" class="chat-bubble-container"></div>
            <button id="voiceBtn" class="voice-assistant-pill" onclick="VoiceAssistant.toggle()">
                <div class="assistant-status">HEY ASSISTANT</div>
                🎙️
            </button>
        `;
        document.body.insertAdjacentHTML('beforeend', html);
    }
};

window.addEventListener('load', () => VoiceAssistant.init());
