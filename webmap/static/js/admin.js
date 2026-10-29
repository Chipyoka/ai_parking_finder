// Admin dashboard: session gating, login, add-site form with live preview
// marker, and site list management (deactivate/reactivate/delete).

const statusEl = document.getElementById("status");
const loginSection = document.getElementById("login-section");
const dashboardSection = document.getElementById("dashboard-section");
const unauthorizedSection = document.getElementById("unauthorized-section");

const loginForm = document.getElementById("login-form");
const loginError = document.getElementById("login-error");
const welcomeMsg = document.getElementById("welcome-msg");
const logoutBtn = document.getElementById("logout-btn");

const addSiteForm = document.getElementById("add-site-form");
const addSiteError = document.getElementById("add-site-error");
const siteNameInput = document.getElementById("site-name");
const siteSourceInput = document.getElementById("site-source");
const siteLatInput = document.getElementById("site-lat");
const siteLngInput = document.getElementById("site-lng");
const siteListEl = document.getElementById("site-list");

const DEFAULT_LAT = -15.4167;
const DEFAULT_LNG = 28.2833;

let previewMap = null;
let previewMarker = null;

function initPreviewMap() {
  previewMap = L.map("preview-map").setView([DEFAULT_LAT, DEFAULT_LNG], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(previewMap);
  previewMarker = L.marker([DEFAULT_LAT, DEFAULT_LNG]).addTo(previewMap);
}

function updatePreviewMarker() {
  const lat = parseFloat(siteLatInput.value);
  const lng = parseFloat(siteLngInput.value);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return;
  previewMarker.setLatLng([lat, lng]);
  previewMap.setView([lat, lng], previewMap.getZoom());
}

siteLatInput.addEventListener("input", updatePreviewMarker);
siteLngInput.addEventListener("input", updatePreviewMarker);

// --- Session handling ------------------------------------------------------

async function checkSession() {
  const res = await fetch("/api/session");
  const data = await res.json();

  if (!data.logged_in) {
    statusEl.textContent = "Not logged in";
    loginSection.style.display = "block";
    dashboardSection.style.display = "none";
    unauthorizedSection.style.display = "none";
    return;
  }

  if (data.role !== "admin") {
    statusEl.textContent = `Logged in as ${data.username}`;
    loginSection.style.display = "none";
    dashboardSection.style.display = "none";
    unauthorizedSection.style.display = "block";
    return;
  }

  statusEl.textContent = `Logged in as ${data.username} (admin)`;
  welcomeMsg.textContent = `Welcome, ${data.username}`;
  loginSection.style.display = "none";
  dashboardSection.style.display = "block";
  unauthorizedSection.style.display = "none";

  if (!previewMap) initPreviewMap();
  loadSites();
}

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.textContent = "";

  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;

  const res = await fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const data = await res.json();
    loginError.textContent = data.error || "Login failed";
    return;
  }

  checkSession();
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  checkSession();
});

// --- Site management --------------------------------------------------------

addSiteForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  addSiteError.textContent = "";

  const payload = {
    name: siteNameInput.value,
    video_source: siteSourceInput.value,
    latitude: parseFloat(siteLatInput.value),
    longitude: parseFloat(siteLngInput.value),
  };

  const res = await fetch("/api/admin/sites", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    addSiteError.textContent = data.error || "Could not add site";
    return;
  }

  addSiteForm.reset();
  loadSites();
});

async function loadSites() {
  const res = await fetch("/api/admin/sites");
  if (!res.ok) return;
  const sites = await res.json();
  renderSiteList(sites);
}

function renderSiteList(sites) {
  siteListEl.innerHTML = "";
  if (sites.length === 0) {
    siteListEl.innerHTML = "<li>No sites registered yet.</li>";
    return;
  }

  sites.forEach((site) => {
    const li = document.createElement("li");

    const info = document.createElement("div");
    info.className = "site-info";
    info.innerHTML = `
      <strong>${site.name}</strong> ${site.is_active ? "" : "(inactive)"}<br>
      Source: ${site.video_source}<br>
      Location: ${site.latitude}, ${site.longitude}
    `;

    const actions = document.createElement("div");
    actions.className = "site-actions";

    const toggleBtn = document.createElement("button");
    toggleBtn.textContent = site.is_active ? "Deactivate" : "Activate";
    toggleBtn.className = site.is_active ? "btn-deactivate" : "";
    toggleBtn.onclick = () => toggleActive(site);

    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "Delete";
    deleteBtn.className = "btn-delete";
    deleteBtn.onclick = () => deleteSite(site);

    actions.appendChild(toggleBtn);
    actions.appendChild(deleteBtn);

    li.appendChild(info);
    li.appendChild(actions);
    siteListEl.appendChild(li);
  });
}

async function toggleActive(site) {
  await fetch(`/api/admin/sites/${site.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_active: !site.is_active }),
  });
  loadSites();
}

async function deleteSite(site) {
  if (!confirm(`Delete "${site.name}"? This cannot be undone.`)) return;
  await fetch(`/api/admin/sites/${site.id}`, { method: "DELETE" });
  loadSites();
}

checkSession();