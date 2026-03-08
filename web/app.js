const API_BASE = "http://localhost:8000";

const liveFrame = document.getElementById("liveFrame");
const askBtn = document.getElementById("askBtn");
const questionInput = document.getElementById("questionInput");
const answerBox = document.getElementById("answer");
const memoryList = document.getElementById("memoryList");
const conversationList = document.getElementById("conversationList");
const resetBtn = document.getElementById("resetBtn");

async function refreshFrame() {
  liveFrame.src = `${API_BASE}/frame?t=${Date.now()}`;
}

async function refreshMemory() {
  try {
    const res = await fetch(`${API_BASE}/memory`);
    const data = await res.json();

    memoryList.innerHTML = "";
    for (const item of data.observations || []) {
      const li = document.createElement("li");
      li.textContent = `${item.timestamp} — ${item.description}`;
      memoryList.appendChild(li);
    }
  } catch (err) {
    memoryList.innerHTML = "<li>Failed to load memory.</li>";
  }
}

async function refreshConversation() {
  try {
    const res = await fetch(`${API_BASE}/conversation`);
    const data = await res.json();

    conversationList.innerHTML = "";
    for (const item of data.history || []) {
      const li = document.createElement("li");
      li.innerHTML = `<strong>Q:</strong> ${item.question}<br><strong>A:</strong> ${item.answer}`;
      conversationList.appendChild(li);
    }
  } catch (err) {
    conversationList.innerHTML = "<li>Failed to load conversation history.</li>";
  }
}

async function resetConversations() {
  try {
    const res = await fetch(`${API_BASE}/reset-conversations`, {
      method: "POST",
    });
    if (res.ok) {
      refreshConversation();
    } else {
      alert("Failed to reset conversations");
    }
  } catch (err) {
    alert("Error resetting conversations");
  }
}

async function askQuestion() {
  const question = questionInput.value.trim();
  if (!question) {
    return;
  }

  askBtn.disabled = true;
  answerBox.textContent = "Thinking...";

  try {
    const res = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    const data = await res.json();
    answerBox.textContent = data.answer || data.detail || "No answer returned.";
    refreshConversation();
  } catch (err) {
    answerBox.textContent = "Request failed. Is the API server running?";
  } finally {
    askBtn.disabled = false;
  }
}

askBtn.addEventListener("click", askQuestion);
questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    askQuestion();
  }
});

resetBtn.addEventListener("click", resetConversations);

setInterval(refreshFrame, 1000);
setInterval(refreshMemory, 2500);
setInterval(refreshConversation, 2500);
refreshFrame();
refreshMemory();
refreshConversation();
