// Public map: loads registered sites from /api/sites, plots one pin per
// site, and updates each pin's popup live as site_update events arrive
// over WebSocket. No login required - this is the driver-facing view.
//
// Loads sites immediately on page load (not only when the socket connects)
// so the page never sits blank if the WebSocket is slow to connect. Also
// polls periodically as a fallback in case a socket event is missed.

const socket = io();
const statusEl = document.getElementById("status");
const summaryListEl = document.getElementById("site-summary-list");

const DEFAULT_LAT = -15.4167;
const DEFAULT_LNG = 28.2833;
const POLL_INTERVAL_MS = 15000;

const map = L.map("map").setView([DEFAULT_LAT, DEFAULT_LNG], 13);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

// site_id -> { marker, site }
const siteState = {};

const COLOR_FREE = "#00e676";      // vibrant green
const COLOR_OCCUPIED = "#ff1744";  // vibrant red
const COLOR_NO_DATA = "#2979ff";   // neutral grey

function pinColor(site) {
  const latest = site.latest;
  if (!latest || latest.free_count + latest.occupied_count === 0) return COLOR_NO_DATA;
  return latest.free_count > 0 ? COLOR_FREE : COLOR_OCCUPIED;
}

function createPinIcon(color) {
  return L.divIcon({
    className: "", // prevent Leaflet's default icon styles from interfering
    html: `
      <div class="pin-marker" style="--pin-color:${color}">
        <span class="pin-pulse"></span>
        <span class="pin-dot"></span>
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -14],
  });
}

function popupContent(site) {
  const latest = site.latest;
  const free = latest ? latest.free_count : 0;
  const total = latest ? latest.free_count + latest.occupied_count : 0;
  const updated = latest ? new Date(latest.event_time).toLocaleTimeString() : "no data yet";
  return `
    <strong>${site.name}</strong><br>
    ${free} free
    <br>
    <span style="font-size:11px;color:#777;">Updated: ${updated}</span>
  `;
}

function renderSummaryList() {
  summaryListEl.innerHTML = "";
  const sites = Object.values(siteState).map((s) => s.site);

  if (sites.length === 0) {
    summaryListEl.innerHTML = "<li class='empty-state'>No sites registered yet.</li>";
    return;
  }

  sites.forEach((site) => {
    const latest = site.latest;
    const free = latest ? latest.free_count : 0;
    const total = latest ? latest.free_count + latest.occupied_count : 0;
    const li = document.createElement("li");
    li.className = free > 0 ? "free" : "occupied";
    li.innerHTML = `<span>${site.name}</span><span>${free} free</span>`;
    summaryListEl.appendChild(li);
  });
}

function addOrUpdateMarker(site) {
  const color = pinColor(site);

  if (siteState[site.id]) {
    siteState[site.id].site = site;
    siteState[site.id].marker.setPopupContent(popupContent(site));
    siteState[site.id].marker.setIcon(createPinIcon(color));
  } else {
    const marker = L.marker([site.latitude, site.longitude], {
      icon: createPinIcon(color),
    })
      .addTo(map)
      .bindPopup(popupContent(site));
    siteState[site.id] = { marker, site };
  }
}

async function loadSites() {
  try {
    const res = await fetch("/api/sites");
    const sites = await res.json();

    sites.forEach((site) => addOrUpdateMarker(site));
    renderSummaryList();

    statusEl.textContent = sites.length > 0
      ? `Showing ${sites.length} site(s) - live`
      : "No sites registered yet";
  } catch (err) {
    statusEl.textContent = "Could not reach server - retrying...";
  }
}

// Load immediately - don't wait for the WebSocket to connect first,
// otherwise the page can sit blank if the socket is slow or fails.
loadSites();
setInterval(loadSites, POLL_INTERVAL_MS);

socket.on("connect", () => {
  loadSites();
});

socket.on("disconnect", () => {
  statusEl.textContent = "Disconnected - showing last known data";
});

socket.on("site_update", (update) => {
  const entry = siteState[update.site_id];
  if (!entry) {
    loadSites(); // a new site was added after page load
    return;
  }
  entry.site.latest = {
    free_count: update.free_count,
    occupied_count: update.occupied_count,
    event_time: new Date().toISOString(),
  };
  addOrUpdateMarker(entry.site);
  renderSummaryList();
});

// --- Night / driving mode toggle --------------------------------------------

const nightToggle = document.getElementById("night-toggle");
if (nightToggle) {
  nightToggle.addEventListener("click", () => {
    document.body.classList.toggle("night-mode");
    const isNight = document.body.classList.contains("night-mode");
    nightToggle.textContent = isNight ? "Day mode" : "Night mode";
    localStorage.setItem("parkingFinderNightMode", isNight ? "1" : "0");
  });

  if (localStorage.getItem("parkingFinderNightMode") === "1") {
    document.body.classList.add("night-mode");
    nightToggle.textContent = "Day mode";
  }
}