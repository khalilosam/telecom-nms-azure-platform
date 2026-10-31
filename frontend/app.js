/**
 * Telecom NMS Dashboard - NOC Operations Controller
 * Author: Osama Khalil (DevOps & Telecom Specialist)
 */

const API_BASE = '/api/v1';

// Seed demo data fallback when running static
const DEMO_SITES = [
  { id: 1, site_code: "NBO-5G-0101", site_name: "Nairobi Central CBD Macro", technology: "5G-NR", region: "East Africa", ip_address: "10.204.12.10", status: "OPERATIONAL" },
  { id: 2, site_code: "NBO-4G-0102", site_name: "Westlands Commercial Hub", technology: "4G-LTE", region: "East Africa", ip_address: "10.204.12.11", status: "OPERATIONAL" },
  { id: 3, site_code: "LSK-5G-0201", site_name: "Lusaka Industrial Area", technology: "5G-NR", region: "Southern Africa", ip_address: "10.205.18.20", status: "DEGRADED" },
  { id: 4, site_code: "LSK-4G-0202", site_name: "Cairo Road Core Site", technology: "4G-LTE", region: "Southern Africa", ip_address: "10.205.18.21", status: "OPERATIONAL" },
  { id: 5, site_code: "WDH-5G-0301", site_name: "Windhoek Independence Ave", technology: "5G-NR", region: "Southern Africa", ip_address: "10.206.24.30", status: "OPERATIONAL" },
  { id: 6, site_code: "LLW-4G-0401", site_name: "Lilongwe Capital City BTS", technology: "4G-LTE", region: "Southern Africa", ip_address: "10.207.30.40", status: "DOWN" },
  { id: 7, site_code: "MBA-4G-0103", site_name: "Mombasa Port Gateway", technology: "4G-LTE", region: "East Africa", ip_address: "10.204.14.15", status: "OPERATIONAL" },
  { id: 8, site_code: "NDL-3G-0205", site_name: "Ndola Copperbelt NodeB", technology: "3G-UMTS", region: "Southern Africa", ip_address: "10.205.22.18", status: "OPERATIONAL" }
];

const DEMO_ALARMS = [
  { id: 101, site_code: "LLW-4G-0401", severity: "CRITICAL", title: "Mains Power Failure - Battery Discharge", raised_at: "2 mins ago" },
  { id: 102, site_code: "LSK-5G-0201", severity: "MAJOR", title: "VSWR High Threshold Exceeded (Sector 2)", raised_at: "14 mins ago" },
  { id: 103, site_code: "MBA-4G-0103", severity: "MINOR", title: "Optical SFP Transceiver Temperature Warning", raised_at: "45 mins ago" },
  { id: 104, site_code: "NBO-5G-0101", severity: "MINOR", title: "BBU Fan Module 3 Minor Speed Deviation", raised_at: "1 hr ago" }
];

let allSites = [];
let allAlarms = [];

document.addEventListener("DOMContentLoaded", () => {
  initClock();
  loadData();
  setupEventListeners();
  setInterval(loadData, 15000); // 15s polling
});

function initClock() {
  const clockEl = document.getElementById("clock");
  function update() {
    const now = new Date();
    clockEl.innerText = now.toUTCString().slice(17, 25) + " UTC";
  }
  update();
  setInterval(update, 1000);
}

async function loadData() {
  try {
    const [sitesRes, alarmsRes] = await Promise.all([
      fetch(`${API_BASE}/sites`).catch(() => null),
      fetch(`${API_BASE}/alarms`).catch(() => null)
    ]);

    if (sitesRes && sitesRes.ok) {
      allSites = await sitesRes.json();
    } else {
      allSites = DEMO_SITES;
    }

    if (alarmsRes && alarmsRes.ok) {
      allAlarms = await alarmsRes.json();
    } else {
      allAlarms = DEMO_ALARMS;
    }
  } catch (e) {
    allSites = DEMO_SITES;
    allAlarms = DEMO_ALARMS;
  }

  updateKpis();
  renderSites();
  renderAlarms();
}

function updateKpis() {
  const total = allSites.length;
  const online = allSites.filter(s => s.status === "OPERATIONAL").length;
  const critical = allAlarms.filter(a => a.severity === "CRITICAL").length;
  const major = allAlarms.filter(a => a.severity === "MAJOR").length;

  document.getElementById("kpi-total-sites").innerText = total;
  document.getElementById("kpi-online-sites").innerText = `${online} / ${total}`;
  document.getElementById("kpi-critical-alarms").innerText = critical;
  document.getElementById("kpi-major-alarms").innerText = major;
}

function renderSites() {
  const tech = document.getElementById("tech-filter").value;
  const region = document.getElementById("region-filter").value;
  const tbody = document.getElementById("sites-table-body");

  const filtered = allSites.filter(s => {
    const matchTech = (tech === "ALL" || s.technology === tech);
    const matchRegion = (region === "ALL" || s.region === region);
    return matchTech && matchRegion;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading">No sites match selected filter criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(s => {
    let statusClass = "badge-operational";
    if (s.status === "DEGRADED") statusClass = "badge-degraded";
    if (s.status === "DOWN") statusClass = "badge-down";

    return `
      <tr>
        <td><strong>${s.site_code}</strong></td>
        <td>${s.site_name}</td>
        <td><span class="badge badge-tech">${s.technology}</span></td>
        <td>${s.region}</td>
        <td>${s.ip_address}</td>
        <td><span class="badge ${statusClass}">${s.status}</span></td>
        <td><button class="btn btn-sm" onclick="pingSite('${s.ip_address}')">Diagnose</button></td>
      </tr>
    `;
  }).join("");
}

function renderAlarms() {
  const container = document.getElementById("alarm-feed-container");
  if (allAlarms.length === 0) {
    container.innerHTML = `<div class="loading">No active alarms. Network fully operational!</div>`;
    return;
  }

  container.innerHTML = allAlarms.map(a => {
    const sevClass = a.severity.toLowerCase();
    return `
      <div class="alarm-card ${sevClass}">
        <div class="alarm-header">
          <span class="alarm-sev sev-${sevClass}">${a.severity}</span>
          <span class="alarm-time">${a.raised_at}</span>
        </div>
        <div class="alarm-site">${a.site_code}</div>
        <div class="alarm-desc">${a.title}</div>
        <div class="alarm-actions">
          <button class="btn btn-sm btn-ack" onclick="ackAlarm(${a.id})">Acknowledge</button>
        </div>
      </div>
    `;
  }).join("");
}

function setupEventListeners() {
  document.getElementById("tech-filter").addEventListener("change", renderSites);
  document.getElementById("region-filter").addEventListener("change", renderSites);
  document.getElementById("refresh-alarms-btn").addEventListener("click", () => {
    loadData();
  });
}

window.pingSite = function(ip) {
  alert(`Initiating ICMP / SNMP probe to RAN Node at ${ip} via Linux VM backend...`);
};

window.ackAlarm = function(id) {
  allAlarms = allAlarms.filter(a => a.id !== id);
  renderAlarms();
  updateKpis();
};
