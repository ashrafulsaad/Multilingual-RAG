const $ = (selector) => document.querySelector(selector);
const state = { documents: [], register: false, token: localStorage.getItem("dhara_token") };

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.token) headers.set("Authorization", `Bearer ${state.token}`);
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    localStorage.removeItem("dhara_token");
    state.token = null;
    location.reload();
  }
  return response;
}

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}

function renderDocuments() {
  const list = $("#documentList");
  $("#documentCount").textContent = `${state.documents.length} document${state.documents.length === 1 ? "" : "s"}`;
  if (!state.documents.length) {
    list.innerHTML = '<div class="list-empty">Your indexed documents will show up here.</div>';
    return;
  }
  list.innerHTML = state.documents.map((doc) => `<div class="document-item"><div><div class="doc-name">${doc.filename}</div><div class="doc-meta">${doc.extracted_characters.toLocaleString()} characters · ${doc.language_hint || "auto"}</div></div><span class="doc-type">${doc.filename.split(".").pop().toUpperCase()}</span></div>`).join("");
}

async function loadDocuments() {
  try {
    const response = await apiFetch("/documents");
    if (!response.ok) throw new Error("Could not load documents");
    state.documents = (await response.json()).documents;
    renderDocuments();
  } catch (error) { showToast(error.message); }
}

function setAuthenticated(token) {
  state.token = token;
  localStorage.setItem("dhara_token", token);
  $("#authScreen").classList.add("hidden");
  loadDocuments();
}

$("#authForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const endpoint = state.register ? "/auth/register" : "/auth/login";
  const response = await fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: $("#username").value, password: $("#password").value }) });
  const payload = await response.json();
  if (!response.ok) return showToast(payload.detail || "Authentication failed");
  if (state.register) {
    state.register = false;
    $("#authAction").textContent = "Sign in";
    $("#authSwitch").textContent = "Need an account? Create one";
    return showToast("Account created. Sign in to continue");
  }
  setAuthenticated(payload.access_token);
});
$("#authSwitch").addEventListener("click", () => { state.register = !state.register; $("#authAction").textContent = state.register ? "Create account" : "Sign in"; $("#authSwitch").textContent = state.register ? "Already have an account? Sign in" : "Need an account? Create one"; });
$("#logoutButton").addEventListener("click", () => { localStorage.removeItem("dhara_token"); location.reload(); });

$("#fileInput").addEventListener("change", (event) => {
  $("#fileName").textContent = event.target.files[0]?.name || "No file selected";
});

$("#uploadForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = $("#fileInput").files[0];
  if (!file) return showToast("Choose a TXT or PDF file first");
  const form = new FormData();
  form.append("file", file);
  if ($("#languageHint").value) form.append("language_hint", $("#languageHint").value);
  const button = event.target.querySelector("button");
  button.disabled = true;
  button.textContent = "Indexing...";
  try {
    const response = await apiFetch("/documents", { method: "POST", body: form });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Upload failed");
    showToast(`${payload.document.filename} added to your library`);
    event.target.reset();
    $("#fileName").textContent = "No file selected";
    await loadDocuments();
  } catch (error) { showToast(error.message); }
  button.disabled = false;
  button.textContent = "Index document";
});

$("#queryForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = $("#question").value.trim();
  if (!question) return;
  const button = event.target.querySelector("button");
  button.disabled = true;
  button.innerHTML = "Thinking...";
  try {
    const response = await apiFetch("/query", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question, top_k: Number($("#topK").value) }) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Query failed");
    $("#answerEmpty").classList.add("hidden");
    $("#answerContent").classList.remove("hidden");
    $("#answerText").textContent = payload.answer;
    $("#sources").innerHTML = payload.sources.map((source) => `<div class="source-card"><strong>${source.filename} · chunk ${source.chunk_index} · ${source.language}</strong><br>${source.text}</div>`).join("");
    $("#metrics").innerHTML = `RETRIEVAL &nbsp; ${payload.latency_ms.retrieval.toFixed(1)} ms<br>GENERATION &nbsp; ${payload.latency_ms.generation.toFixed(1)} ms<br>TOTAL &nbsp; ${payload.latency_ms.total.toFixed(1)} ms<br><br>SOURCES &nbsp; ${payload.sources.length}`;
    $("#latencyLabel").textContent = `${payload.sources.length} source chunks · ${payload.latency_ms.total.toFixed(0)} ms total`;
    $("#answerSection").scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (error) { showToast(error.message); }
  button.disabled = false;
  button.innerHTML = "<span>Ask Dhara</span><span>→</span>";
});

document.querySelectorAll("[data-question]").forEach((button) => button.addEventListener("click", () => { $("#question").value = button.dataset.question; $("#question").focus(); }));
$("#refreshButton").addEventListener("click", loadDocuments);
if (state.token) { $("#authScreen").classList.add("hidden"); loadDocuments(); }