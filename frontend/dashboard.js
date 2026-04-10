const API = "http://localhost:5000";
let enrollFiles = [];

// ── Init ──
document.addEventListener("DOMContentLoaded", () => {
  const now  = new Date();
  const opts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  const dateStr = now.toLocaleDateString('en-IN', opts);

  document.getElementById("today-date").textContent    = dateStr;
  document.getElementById("checkin-date").textContent  = dateStr;
  document.getElementById("report-date").value         = now.toISOString().split("T")[0];

  checkServer();
  loadTodayReport();
  startCamera();
});

// ── Server Status ──
async function checkServer() {
  const el = document.getElementById("server-status");
  try {
    const r = await fetch(`${API}/api/report/today`);
    if (r.ok) {
      el.textContent   = "online ✓";
      el.style.color   = "var(--green-mid)";
    } else throw new Error();
  } catch {
    el.textContent = "offline ✗";
    el.style.color = "var(--red)";
  }
}

// ── Navigation ──
function showPage(name, btn) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
  document.getElementById("page-" + name).classList.add("active");
  if (btn) btn.classList.add("active");

  if (name === "students") loadStudents();
  if (name === "reports")  loadReport();
  if (name === "home")     loadTodayReport();
}

// ── Today Stats + Home Table ──
async function loadTodayReport() {
  try {
    const r    = await fetch(`${API}/api/report/today`);
    const data = await r.json();

    const present = data.filter(d => d.status === "present").length;
    const absent  = data.filter(d => d.status === "absent").length;
    const total   = data.length;
    const rate    = total > 0 ? Math.round((present / total) * 100) + "%" : "—";

    document.getElementById("stat-present").textContent = present;
    document.getElementById("stat-absent").textContent  = absent;
    document.getElementById("stat-total").textContent   = total;
    document.getElementById("stat-rate").textContent    = rate;

    const tbody = document.getElementById("home-table-body");
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:32px">No records yet today</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map(d => `
      <tr>
        <td style="font-family:'DM Mono',monospace;font-size:13px">${d.student_id}</td>
        <td>${d.name || "—"}</td>
        <td><span class="badge badge-${d.status}">${d.status}</span></td>
        <td style="color:var(--muted);font-size:13px">${d.time ? new Date(d.time).toLocaleTimeString() : "—"}</td>
      </tr>`).join("");
  } catch {
    document.getElementById("home-table-body").innerHTML =
      `<tr><td colspan="4" style="text-align:center;color:var(--red);padding:32px">Cannot reach server</td></tr>`;
  }
}

// ── Camera ──
async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    document.getElementById("video").srcObject = stream;
  } catch {
    console.warn("Camera not available");
  }
}

async function capture() {
  const captureText   = document.getElementById("capture-text");
  const captureSpinner = document.getElementById("capture-spinner");
  const captureAlert  = document.getElementById("capture-alert");
  const video  = document.getElementById("video");
  const canvas = document.getElementById("canvas");

  captureSpinner.style.display = "block";
  captureText.textContent      = "Processing...";
  captureAlert.className       = "alert";

  canvas.getContext("2d").drawImage(video, 0, 0, 640, 480);

  canvas.toBlob(async blob => {
    const form = new FormData();
    form.append("photo", blob, "checkin.jpg");
    try {
      const r    = await fetch(`${API}/api/attend`, { method: "POST", body: form });
      const data = await r.json();

      if (data.status === "present") {
        captureAlert.className   = "alert success";
        captureAlert.textContent = `✅ ${data.student_id} marked present!`;
        addLog(data.student_id, "present");
        loadTodayReport();
      } else if (data.status === "already_marked") {
        captureAlert.className   = "alert success";
        captureAlert.textContent = `ℹ️ ${data.student_id} already marked present today.`;
      } else {
        captureAlert.className   = "alert error";
        captureAlert.textContent = "❌ Face not recognized.";
        addLog("Unknown", "absent");
      }
    } catch {
      captureAlert.className   = "alert error";
      captureAlert.textContent = "❌ Server error. Is Flask running?";
    } finally {
      captureSpinner.style.display = "none";
      captureText.textContent      = "📸   Capture & Mark Attendance";
    }
  }, "image/jpeg");
}

function addLog(name, status) {
  const list = document.getElementById("log-list");
  const time = new Date().toLocaleTimeString();
  const item = document.createElement("div");
  item.className = `log-item ${status}`;
  item.innerHTML = `
    <div class="log-dot"></div>
    <div class="log-name">${name}</div>
    <div class="log-time">${time}</div>`;
  if (list.children.length === 1 && list.children[0].querySelector === undefined) list.innerHTML = "";
  list.insertBefore(item, list.firstChild);
}

// ── Enroll ──
function addEnrollPhotos(input) {
  Array.from(input.files).forEach(f => {
    if (!enrollFiles.find(e => e.name === f.name && e.size === f.size)) {
      enrollFiles.push(f);
    }
  });
  input.value = "";
  renderEnrollPreviews();
  updateEnrollCounter();
}

function removeEnrollPhoto(i) {
  enrollFiles.splice(i, 1);
  renderEnrollPreviews();
  updateEnrollCounter();
}

function renderEnrollPreviews() {
  const preview = document.getElementById("enroll-preview");
  preview.innerHTML = "";
  enrollFiles.forEach((f, i) => {
    const wrap = document.createElement("div");
    wrap.className = "thumb-wrap";

    const img = document.createElement("img");
    img.src   = URL.createObjectURL(f);

    const btn = document.createElement("button");
    btn.className = "thumb-remove";
    btn.innerHTML = "✕";
    btn.onclick   = e => { e.stopPropagation(); removeEnrollPhoto(i); };

    wrap.appendChild(img);
    wrap.appendChild(btn);
    preview.appendChild(wrap);
  });
}

function updateEnrollCounter() {
  const counter     = document.getElementById("enroll-counter");
  const counterText = document.getElementById("enroll-counter-text");
  const n           = enrollFiles.length;
  if (!n) { counter.style.display = "none"; return; }
  counter.style.display = "inline-flex";
  counter.className     = "photo-counter" + (n < 3 ? " warn" : "");
  counterText.textContent = `${n} photo${n > 1 ? "s" : ""} selected${n < 3 ? " — add at least 3" : ""}`;
}

async function enrollStudent() {
  const id        = document.getElementById("e-id").value.trim();
  const name      = document.getElementById("e-name").value.trim();
  const cls       = document.getElementById("e-class").value.trim();
  const alertEl   = document.getElementById("enroll-alert");
  const btn       = document.getElementById("enroll-btn");
  const spinner   = document.getElementById("enroll-spinner");
  const btnText   = document.getElementById("enroll-btn-text");

  alertEl.className = "alert";

  if (!id || !name) {
    alertEl.className   = "alert error";
    alertEl.textContent = "❌ Student ID and Name are required.";
    return;
  }

  if (enrollFiles.length < 3) {
    alertEl.className   = "alert error";
    alertEl.textContent = "❌ Upload at least 3 photos for accuracy.";
    return;
  }

  btn.disabled          = true;
  spinner.style.display = "block";
  btnText.textContent   = "Enrolling...";

  const form = new FormData();
  form.append("student_id", id);
  form.append("name", name);
  form.append("class_", cls);
  enrollFiles.forEach(f => form.append("photos", f));

  try {
    const r    = await fetch(`${API}/api/enroll`, { method: "POST", body: form });
    const data = await r.json();

    if (r.ok) {
      alertEl.className   = "alert success";
      alertEl.textContent = "✅ " + data.message;
      document.getElementById("e-id").value    = "";
      document.getElementById("e-name").value  = "";
      document.getElementById("e-class").value = "";
      enrollFiles = [];
      renderEnrollPreviews();
      updateEnrollCounter();
      loadTodayReport();
    } else {
      alertEl.className   = "alert error";
      alertEl.textContent = "❌ " + (data.error || "Enrollment failed.");
    }
  } catch {
    alertEl.className   = "alert error";
    alertEl.textContent = "❌ Cannot reach server.";
  } finally {
    btn.disabled          = false;
    spinner.style.display = "none";
    btnText.textContent   = "Enroll Student";
  }
}

// ── Students ──
async function loadStudents() {
  const tbody = document.getElementById("students-body");
  tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:32px">Loading...</td></tr>`;
  try {
    const r    = await fetch(`${API}/api/students`);
    const data = await r.json();
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:32px">No students enrolled yet</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map(s => `
      <tr>
        <td style="font-family:'DM Mono',monospace;font-size:13px">${s.id}</td>
        <td>${s.name}</td>
        <td><span class="badge badge-unknown">${s.class_ || "—"}</span></td>
        <td style="color:var(--muted);font-size:13px">${s.enrolled ? new Date(s.enrolled).toLocaleDateString() : "—"}</td>
      </tr>`).join("");
  } catch {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:var(--red);padding:32px">Cannot reach server</td></tr>`;
  }
}

// ── Reports ──
async function loadReport() {
  const date  = document.getElementById("report-date").value;
  const tbody = document.getElementById("report-body");
  if (!date) return;
  tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:32px">Loading...</td></tr>`;
  try {
    const r    = await fetch(`${API}/api/report/date?date=${date}`);
    const data = await r.json();
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:32px">No records for this date</td></tr>`;
      return;
    }
    tbody.innerHTML = data.map(d => `
      <tr>
        <td style="font-family:'DM Mono',monospace;font-size:13px">${d.student_id}</td>
        <td>${d.name || "—"}</td>
        <td style="color:var(--muted)">${d.date || date}</td>
        <td><span class="badge badge-${d.status}">${d.status}</span></td>
        <td style="color:var(--muted);font-size:13px">${d.time ? new Date(d.time).toLocaleTimeString() : "—"}</td>
      </tr>`).join("");
  } catch {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--red);padding:32px">Cannot reach server</td></tr>`;
  }
}

function exportCSV() {
  window.open(`${API}/api/report/export`, "_blank");
}
