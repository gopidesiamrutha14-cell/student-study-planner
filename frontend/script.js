
const taskForm = document.getElementById("taskForm");
const taskList = document.getElementById("taskList");

// Load dashboard counts
async function loadDashboard() {
    try {
        const response = await fetch("/api/dashboard");
        if (!response.ok) throw new Error("Dashboard request failed");

        const data = await response.json();

        document.getElementById("totalTasks").textContent =
            data.totalTasks ?? 0;
        document.getElementById("pendingTasks").textContent =
            data.pendingTasks ?? 0;
        document.getElementById("completedTasks").textContent =
            data.completedTasks ?? 0;
    } catch (error) {
        console.error("Dashboard error:", error);
    }
}

// Load and display tasks
async function loadTasks() {
    taskList.textContent = "Loading tasks...";

    try {
        const response = await fetch("/api/tasks");
        if (!response.ok) throw new Error("Could not load tasks");

        const tasks = await response.json();
        taskList.replaceChildren();

        if (tasks.length === 0) {
            taskList.textContent =
                "No tasks yet. Add your first study task!";
            return;
        }

        tasks.forEach(task => {
            const item = document.createElement("div");
            item.className = "task-item";

            const details = document.createElement("div");
            const name = document.createElement("strong");
            name.textContent = task.task_name;

            const info = document.createElement("p");
            info.textContent =
                `${task.subject || "No subject"} • Deadline: ${
                    task.deadline || "Not set"
                } • ${task.status}`;

            details.append(name, info);

            const actions = document.createElement("div");
            actions.className = "task-actions";

            // Complete button
            if (task.status === "Pending") {
                const completeButton = document.createElement("button");
                completeButton.className = "complete";
                completeButton.textContent = "Complete";

                completeButton.addEventListener("click", () =>
                    updateTask(task.task_id, "PATCH", {
                        status: "Completed"
                    })
                );

                actions.appendChild(completeButton);
            }

            // Delete button
            const deleteButton = document.createElement("button");
            deleteButton.className = "delete";
            deleteButton.textContent = "Delete";

            deleteButton.addEventListener("click", () => {
                if (confirm("Are you sure you want to delete this task?")) {
                    updateTask(task.task_id, "DELETE");
                }
            });

            actions.appendChild(deleteButton);
            item.append(details, actions);
            taskList.appendChild(item);
        });
    } catch (error) {
        console.error("Tasks error:", error);
        taskList.textContent =
            "Could not load tasks. Check the Flask terminal.";
    }
}

// Add a new task
taskForm.addEventListener("submit", async event => {
    event.preventDefault();

    const task = {
        task_name: document.getElementById("taskName").value.trim(),
        subject: document.getElementById("subject").value.trim(),
        deadline: document.getElementById("deadline").value
    };

    try {
        const response = await fetch("/api/tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(task)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Could not add task");
        }

        taskForm.reset();
        await loadTasks();
        await loadDashboard();

        alert("Study task added successfully!");
    } catch (error) {
        console.error("Add task error:", error);
        alert("Could not add task: " + error.message);
    }
});

// Complete or delete a task
async function updateTask(taskId, method, data = null) {
    try {
        const options = { method };

        if (data) {
            options.headers = {
                "Content-Type": "application/json"
            };
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`/api/tasks/${taskId}`, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Operation failed");
        }

        await loadTasks();
        await loadDashboard();
    } catch (error) {
        console.error("Update task error:", error);
        alert(error.message);
    }
}

// Initial page load
loadTasks();
loadDashboard();
