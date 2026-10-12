
const API_URL = "";
const USER_ID = 1;

// Get HTML elements
const taskForm = document.getElementById("taskForm");
const taskList = document.getElementById("taskList");
const sessionForm = document.getElementById("sessionForm");
const sessionList = document.getElementById("sessionList");


// Display a friendly error message
function showError(message) {
    alert(message);
}


// Load dashboard statistics
async function loadDashboard() {
    try {
        const response = await fetch(
            `${API_URL}/dashboard/${USER_ID}`
        );

        if (!response.ok) {
            throw new Error("Could not load dashboard.");
        }

        const data = await response.json();

        document.getElementById("totalTasks").textContent =
            data.total_tasks;

        document.getElementById("pendingTasks").textContent =
            data.pending_tasks;

        document.getElementById("completedTasks").textContent =
            data.completed_tasks;

        const totalMinutes = Number(data.total_study_minutes) || 0;
        const hours = Math.floor(totalMinutes / 60);
        const minutes = totalMinutes % 60;

        document.getElementById("totalStudyTime").textContent =
            hours > 0
                ? `${hours} hr ${minutes} min`
                : `${minutes} minutes`;

    } catch (error) {
        console.error("Dashboard error:", error);
    }
}


// Display study tasks
function displayTasks(tasks) {
    taskList.replaceChildren();

    if (tasks.length === 0) {
        taskList.textContent = "No study tasks yet.";
        return;
    }

    tasks.forEach(function (task) {
        const item = document.createElement("li");
        const details = document.createElement("p");

        details.textContent =
            `${task.task_name} | ${task.subject} | ` +
            `Deadline: ${task.deadline} | Status: ${task.status}`;

        item.appendChild(details);

        // Mark pending task as completed
        if (task.status !== "Completed") {
            const completeButton = document.createElement("button");

            completeButton.textContent = "Mark Completed";

            completeButton.addEventListener("click", function () {
                completeTask(task.task_id);
            });

            item.appendChild(completeButton);
        }

        // Delete task
        const deleteButton = document.createElement("button");

        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", function () {
            deleteTask(task.task_id);
        });

        item.appendChild(deleteButton);
        taskList.appendChild(item);
    });
}


// Load study tasks
async function loadTasks() {
    try {
        const response = await fetch(
            `${API_URL}/tasks/${USER_ID}`
        );

        if (!response.ok) {
            throw new Error("Could not load tasks.");
        }

        const tasks = await response.json();
        displayTasks(tasks);

    } catch (error) {
        console.error("Tasks error:", error);
        taskList.textContent = "Unable to load study tasks.";
    }
}


// Add a study task
taskForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const taskName =
        document.getElementById("task").value.trim();

    const subject =
        document.getElementById("subject").value.trim();

    const deadline =
        document.getElementById("deadline").value;

    if (!taskName || !subject || !deadline) {
        showError("Please fill in all task details.");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/tasks`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: USER_ID,
                task_name: taskName,
                subject: subject,
                deadline: deadline
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Could not add study task."
            );
        }

        taskForm.reset();

        await loadTasks();
        await loadDashboard();

        alert("Study task added successfully!");

    } catch (error) {
        showError(error.message);
    }
});


// Mark a task as completed
async function completeTask(taskId) {
    try {
        const response = await fetch(
            `${API_URL}/tasks/${taskId}/complete`,
            {
                method: "PUT"
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Could not complete task."
            );
        }

        await loadTasks();
        await loadDashboard();

    } catch (error) {
        showError(error.message);
    }
}


// Delete a study task
async function deleteTask(taskId) {
    if (!confirm("Are you sure you want to delete this task?")) {
        return;
    }

    try {
        const response = await fetch(
            `${API_URL}/tasks/${taskId}`,
            {
                method: "DELETE"
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Could not delete task."
            );
        }

        await loadTasks();
        await loadDashboard();

        alert("Study task deleted successfully!");

    } catch (error) {
        showError(error.message);
    }
}


// Display study sessions
function displaySessions(sessions) {
    sessionList.replaceChildren();

    if (sessions.length === 0) {
        sessionList.textContent =
            "No study sessions recorded yet.";
        return;
    }

    sessions.forEach(function (session) {
        const item = document.createElement("li");

        item.textContent =
            `${session.subject} | Date: ${session.study_date} | ` +
            `${session.duration_minutes} minutes` +
            (session.notes ? ` | Notes: ${session.notes}` : "");

        sessionList.appendChild(item);
    });
}


// Load study sessions
async function loadSessions() {
    try {
        const response = await fetch(
            `${API_URL}/sessions/${USER_ID}`
        );

        if (!response.ok) {
            throw new Error("Could not load study sessions.");
        }

        const sessions = await response.json();
        displaySessions(sessions);

    } catch (error) {
        console.error("Study sessions error:", error);
        sessionList.textContent =
            "Unable to load study sessions.";
    }
}


// Add a study session
sessionForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const subject =
        document.getElementById("sessionSubject").value.trim();

    const studyDate =
        document.getElementById("studyDate").value;

    const duration =
        Number(document.getElementById("duration").value);

    const notes =
        document.getElementById("notes").value.trim();

    if (
        !subject ||
        !studyDate ||
        !Number.isInteger(duration) ||
        duration <= 0
    ) {
        showError(
            "Enter a subject, study date, and a positive whole number of minutes."
        );
        return;
    }

    try {
        const response = await fetch(`${API_URL}/sessions`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: USER_ID,
                subject: subject,
                study_date: studyDate,
                duration_minutes: duration,
                notes: notes
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error || "Could not save study session."
            );
        }

        sessionForm.reset();

        await loadSessions();
        await loadDashboard();

        alert("Study session saved successfully!");

    } catch (error) {
        showError(error.message);
    }
});


// Load existing data when the page opens
async function initializeApp() {
    await Promise.all([
        loadTasks(),
        loadSessions(),
        loadDashboard()
    ]);
}

initializeApp();
