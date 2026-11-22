const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
const toast = document.getElementById("toast");

function notify(message, isError = false) {
  if (!toast) return;
  toast.textContent = message;
  toast.className = "toast show" + (isError ? " error" : "");
  window.setTimeout(() => toast.className = "toast", 5000);
}
async function api(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
function setEnabled(enabled) {
  document.getElementById("automation-value").textContent = enabled ? "Running" : "Paused";
  document.getElementById("automation-hint").textContent = enabled ? "Posting is enabled" : "Waiting for you to start";
  document.getElementById("status-pill").textContent = enabled ? "ACTIVE" : "PAUSED";
  document.getElementById("status-pill").className = "pill " + (enabled ? "pill-green" : "pill-gray");
  document.getElementById("side-status").textContent = enabled ? "Automation active" : "Automation paused";
  document.getElementById("side-dot").className = enabled ? "on" : "";
  document.getElementById("start-btn").disabled = enabled;
  document.getElementById("pause-btn").disabled = !enabled;
}
document.getElementById("start-btn")?.addEventListener("click", async () => {
  try { await api("/api/control", {action:"start"}); setEnabled(true); notify("Automation started."); }
  catch(e) { notify(e.message, true); }
});
document.getElementById("pause-btn")?.addEventListener("click", async () => {
  try { await api("/api/control", {action:"pause"}); setEnabled(false); notify("Automation paused."); }
  catch(e) { notify(e.message, true); }
});
document.getElementById("save-settings")?.addEventListener("click", async () => {
  try {
    const interval = Number(document.getElementById("interval-input").value);
    const limit = Number(document.getElementById("limit-input").value);
    await api("/api/settings", {interval_minutes:interval, daily_limit:limit});
    document.getElementById("interval-value").textContent = interval;
    document.getElementById("daily-limit-value").textContent = limit;
    notify("Settings saved.");
  } catch(e) { notify(e.message, true); }
});
document.getElementById("generate-btn")?.addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true; button.textContent = "Generating image…";
  try {
    const data = await api("/api/generate");
    notify("New post and image created. Refreshing the list…");
    window.location.reload();
  } catch(e) { notify(e.message, true); }
  finally { button.disabled = false; button.textContent = "＋ Generate a post"; }
});
document.getElementById("refresh-btn")?.addEventListener("click", () => window.location.reload());
document.querySelectorAll("[data-publish]").forEach(button => {
  button.addEventListener("click", async () => {
    button.disabled = true; button.textContent = "Publishing…";
    try {
      await api("/api/publish/" + button.dataset.publish);
      notify("Post published to Facebook.");
      window.location.reload();
    } catch(e) { notify(e.message, true); button.disabled = false; button.textContent = "Publish"; }
  });
});
async function refreshStatus() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok) return;
    const data = await response.json();
    setEnabled(data.enabled);
    document.getElementById("published-count").textContent = data.today_published;
    if (data.next_run_at) document.getElementById("next-run").textContent = new Date(data.next_run_at).toLocaleString();
    if (data.last_error) notify("Last worker error: " + data.last_error, true);
  } catch (_) {}
}
window.setInterval(refreshStatus, 30000);
