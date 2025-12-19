const statusText = document.getElementById("status-text");
const statusPercent = document.getElementById("status-percent");
const statusBar = document.getElementById("status-bar");
const statusLog = document.getElementById("status-log");
const lastUpdated = document.getElementById("last-updated");

function updateUI(data) {
  if (data.status) statusText.innerText = data.status;
  if (data.progress !== undefined) {
    statusPercent.innerText = `${data.progress}%`;
    statusBar.style.width = `${data.progress}%`;
  }

  if (data.logs && Array.isArray(data.logs)) {
    statusLog.innerHTML = data.logs
      .map((log) => `<div><span class="text-[#63b3ed]">></span> ${log}</div>`)
      .join("");
    statusLog.scrollTop = statusLog.scrollHeight;
  }

  lastUpdated.innerText = new Date().toLocaleTimeString();
}

// Use polling for status updates from backend
async function fetchStatus() {
  try {
    const response = await fetch("/status");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    updateUI(data);
    statusText.classList.remove("text-status-error");
  } catch (err) {
    console.error("Polling error:", err);
    statusText.innerText = "Connection lost. Retrying...";
    statusText.classList.add("text-status-error");
  }
}

// Start polling every 1 second
fetchStatus();
const pollingInterval = setInterval(fetchStatus, 1000);
