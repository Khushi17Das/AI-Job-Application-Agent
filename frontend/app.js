/**
 * AI JOB APPLICATION AGENT — FRONTEND LOGIC
 */

// Rock-solid API Base detection:
// Only use http://127.0.0.1:8000 if explicitly running on local machine via Live Server (port 5500/5501).
// On Railway.app or any deployed server (https://...up.railway.app), ALWAYS use relative path ("").
const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const isLiveServerPort = ["5500", "5501", "5502", "5503", "3000", "5173"].includes(window.location.port);

const API_BASE = (isLocalhost && isLiveServerPort) ? "http://127.0.0.1:8000" : "";

console.log("AI Job Application Agent loaded. API_BASE:", API_BASE || "(relative root)");

let currentResumeId = null;
let currentResumeText = "";
let currentMatchScore = 0;

document.addEventListener("DOMContentLoaded", () => {
    initDragAndDrop();
    initEventListeners();
    fetchLatestResume();
    loadDashboardStats();
    loadApplications();
});

// Toast Notification Helper
function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// DRAG AND DROP HANDLERS
function initDragAndDrop() {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("cv-file-input");

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            uploadCVFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadCVFile(e.target.files[0]);
        }
    });
}

function initEventListeners() {
    document.getElementById("btn-analyze-job").addEventListener("click", analyzeJobDescription);
    document.getElementById("btn-analyze-match").addEventListener("click", analyzeMatch);
    document.getElementById("btn-generate-all-answers").addEventListener("click", generateAllAnswers);
    document.getElementById("btn-quick-save-app").addEventListener("click", quickTrackJob);
}

// 1. RESUME UPLOAD & FETCH
async function uploadCVFile(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
        showToast("Uploading and extracting CV text...", "success");
        const response = await fetch(`${API_BASE}/api/resume/upload`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to upload resume.");
        }

        const data = await response.json();
        currentResumeId = data.resume_id;

        displayCVInfo(data.filename, data.total_characters, data.text_snippet);
        showToast("CV text extracted successfully!");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function fetchLatestResume() {
    try {
        const response = await fetch(`${API_BASE}/api/resume/latest`);
        if (response.ok) {
            const data = await response.json();
            currentResumeId = data.id;
            currentResumeText = data.extracted_text;
            const snippet = data.extracted_text.substring(0, 200) + "...";
            displayCVInfo(data.filename, data.extracted_text.length, snippet);
        }
    } catch (e) {
        // Silent catch if no resume exists yet
    }
}

function displayCVInfo(filename, length, snippet) {
    document.getElementById("cv-filename").textContent = filename;
    document.getElementById("cv-char-count").textContent = length.toLocaleString();
    document.getElementById("cv-snippet-text").textContent = snippet;
    document.getElementById("cv-status-box").classList.remove("hidden");
}

// 2. JOB ANALYSIS
async function analyzeJobDescription() {
    const jdText = document.getElementById("jd-text").value.trim();
    if (!jdText) {
        showToast("Please paste a job description first.", "error");
        return;
    }

    const spinner = document.getElementById("spinner-job");
    spinner.classList.remove("hidden");

    try {
        const response = await fetch(`${API_BASE}/api/analyze/job`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_description: jdText })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to analyze job description.");
        }

        const data = await response.json();

        // Populate fields
        document.getElementById("req-role").textContent = data.role || "Not Specified";
        renderTags("req-required-skills", data.required_skills);
        renderTags("req-preferred-skills", data.preferred_skills);
        renderList("req-experience-list", data.experience_requirements);

        document.getElementById("job-analysis-output").classList.remove("hidden");
        showToast("Job requirements extracted successfully!");
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        spinner.classList.add("hidden");
    }
}

// 3. MATCH & SKILL GAP ANALYSIS
async function analyzeMatch() {
    const jdText = document.getElementById("jd-text").value.trim();
    if (!jdText) {
        showToast("Please enter a job description in Step 2.", "error");
        return;
    }
    if (!currentResumeId) {
        showToast("Please upload a CV in Step 1 first.", "error");
        return;
    }

    const spinner = document.getElementById("spinner-match");
    spinner.classList.remove("hidden");

    try {
        const response = await fetch(`${API_BASE}/api/analyze/match`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_description: jdText,
                resume_id: currentResumeId
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to calculate match score.");
        }

        const data = await response.json();
        currentMatchScore = data.match_score;

        // Render Score
        const circle = document.getElementById("score-circle");
        circle.style.setProperty("--score-pct", data.match_score);
        document.getElementById("match-score-num").textContent = `${data.match_score}%`;

        // Render Skill Gap Categories
        renderTags("gap-strong-list", data.skill_gap.strong_match, "badge-success");
        renderTags("gap-partial-list", data.skill_gap.partial_match, "badge-warning");
        renderTags("gap-missing-list", data.skill_gap.missing, "badge-danger");

        // Render Relevant Experience Highlights
        renderList("relevant-exp-list", data.relevant_experience);

        document.getElementById("match-output").classList.remove("hidden");
        showToast("Match analysis complete!");
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        spinner.classList.add("hidden");
    }
}

// 4. GENERATE TAILORED ANSWERS
async function generateAllAnswers() {
    const jdText = document.getElementById("jd-text").value.trim();
    if (!jdText) {
        showToast("Please enter a job description in Step 2.", "error");
        return;
    }
    if (!currentResumeId) {
        showToast("Please upload a CV in Step 1 first.", "error");
        return;
    }

    const spinner = document.getElementById("spinner-answers");
    spinner.classList.remove("hidden");

    try {
        const response = await fetch(`${API_BASE}/api/generate/answers`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_description: jdText,
                resume_id: currentResumeId
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to generate application answers.");
        }

        const data = await response.json();

        document.getElementById("ans-fit").value = data.why_good_fit || "";
        document.getElementById("ans-exp").value = data.relevant_experience || "";
        document.getElementById("ans-project").value = data.relevant_project || "";
        document.getElementById("ans-role").value = data.why_this_role || "";
        document.getElementById("ans-message").value = data.recruiter_message || "";

        showToast("All tailored application answers generated!");
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        spinner.classList.add("hidden");
    }
}

// 5. CLAIM VERIFICATION
async function verifyAnswer(textareaId, badgeContainerId) {
    const answerText = document.getElementById(textareaId).value.trim();
    const badgeBox = document.getElementById(badgeContainerId);

    if (!answerText) {
        showToast("Cannot verify an empty response.", "error");
        return;
    }
    if (!currentResumeId) {
        showToast("Please upload a CV first for verification comparison.", "error");
        return;
    }

    badgeBox.className = "verify-result";
    badgeBox.innerHTML = `<em>Verifying claims against CV...</em>`;
    badgeBox.classList.remove("hidden");

    try {
        const response = await fetch(`${API_BASE}/api/verify/answer`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                answer_text: answerText,
                resume_id: currentResumeId
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Verification failed.");
        }

        const data = await response.json();

        if (data.verified) {
            badgeBox.className = "verify-result verify-success";
            badgeBox.innerHTML = `✓ <strong>Verified Grounded</strong> — All claims in this answer are supported by your CV.`;
        } else {
            badgeBox.className = "verify-result verify-warning";
            let issuesHtml = data.issues.map(i => `<li>${i}</li>`).join('');
            badgeBox.innerHTML = `⚠️ <strong>Unsupported Claims Detected:</strong><ul class="styled-list mt-1">${issuesHtml}</ul>`;
        }
    } catch (err) {
        badgeBox.className = "verify-result verify-warning";
        badgeBox.textContent = `Verification Error: ${err.message}`;
    }
}

// 6. APPLICATION TRACKER & DASHBOARD
async function loadDashboardStats() {
    try {
        const res = await fetch(`${API_BASE}/api/applications/stats`);
        if (res.ok) {
            const stats = await res.json();
            document.getElementById("stat-total").textContent = stats.total_applications;
            document.getElementById("stat-saved").textContent = stats.saved;
            document.getElementById("stat-applied").textContent = stats.applied;
            document.getElementById("stat-interview").textContent = stats.interview;
            document.getElementById("stat-rejected").textContent = stats.rejected;
            document.getElementById("stat-offer").textContent = stats.offer;
        }
    } catch (e) {
        console.error("Failed to load dashboard stats", e);
    }
}

async function loadApplications() {
    try {
        const res = await fetch(`${API_BASE}/api/applications`);
        if (!res.ok) return;

        const apps = await res.json();
        const tbody = document.getElementById("app-table-body");

        if (apps.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No application records found. Add one above!</td></tr>`;
            return;
        }

        tbody.innerHTML = apps.map(app => `
            <tr>
                <td><strong>${escapeHtml(app.company)}</strong></td>
                <td>${escapeHtml(app.job_title)}</td>
                <td>${app.match_score !== null ? `<span class="badge-pill bg-dark">${app.match_score}%</span>` : '--'}</td>
                <td>
                    <select class="form-control btn-sm" onchange="updateAppStatus(${app.id}, this.value)">
                        <option value="Saved" ${app.status === 'Saved' ? 'selected' : ''}>Saved</option>
                        <option value="Applied" ${app.status === 'Applied' ? 'selected' : ''}>Applied</option>
                        <option value="Interview" ${app.status === 'Interview' ? 'selected' : ''}>Interview</option>
                        <option value="Rejected" ${app.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
                        <option value="Offer" ${app.status === 'Offer' ? 'selected' : ''}>Offer</option>
                    </select>
                </td>
                <td>${app.date_applied || app.created_at.substring(0, 10)}</td>
                <td>
                    <button class="btn btn-sm btn-outline text-red" onclick="deleteApp(${app.id})">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error("Failed to load applications", e);
    }
}

function quickTrackJob() {
    const company = document.getElementById("company-name-input").value || "Target Company";
    const role = document.getElementById("job-title-input").value || document.getElementById("req-role").textContent || "Software Role";
    const jd = document.getElementById("jd-text").value;

    document.getElementById("form-app-id").value = "";
    document.getElementById("form-company").value = company;
    document.getElementById("form-role").value = role;
    document.getElementById("form-score").value = currentMatchScore || 80;
    document.getElementById("form-status").value = "Saved";
    document.getElementById("form-notes").value = jd ? "Analyzed JD: " + jd.substring(0, 150) + "..." : "";
    document.getElementById("form-date").value = new Date().toISOString().substring(0, 10);

    toggleNewAppModal(true);
}

function toggleNewAppModal(show) {
    const modal = document.getElementById("app-modal");
    if (show) {
        modal.classList.remove("hidden");
    } else {
        modal.classList.add("hidden");
        document.getElementById("app-form").reset();
    }
}

async function saveApplication(e) {
    e.preventDefault();
    const payload = {
        company: document.getElementById("form-company").value,
        job_title: document.getElementById("form-role").value,
        job_url: document.getElementById("form-url").value || null,
        match_score: document.getElementById("form-score").value ? parseInt(document.getElementById("form-score").value) : null,
        status: document.getElementById("form-status").value,
        notes: document.getElementById("form-notes").value || null,
        date_applied: document.getElementById("form-date").value || null
    };

    try {
        const res = await fetch(`${API_BASE}/api/applications`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Failed to save application entry.");

        showToast("Application tracked successfully!");
        toggleNewAppModal(false);
        loadApplications();
        loadDashboardStats();
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function updateAppStatus(id, newStatus) {
    try {
        const res = await fetch(`${API_BASE}/api/applications/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            showToast("Application status updated.");
            loadDashboardStats();
        }
    } catch (e) {
        showToast("Status update failed.", "error");
    }
}

async function deleteApp(id) {
    if (!confirm("Are you sure you want to delete this tracked application?")) return;
    try {
        const res = await fetch(`${API_BASE}/api/applications/${id}`, {
            method: "DELETE"
        });
        if (res.ok) {
            showToast("Application deleted.");
            loadApplications();
            loadDashboardStats();
        }
    } catch (e) {
        showToast("Delete failed.", "error");
    }
}

// HELPER RENDERERS
function renderTags(containerId, items, badgeClass = "") {
    const el = document.getElementById(containerId);
    if (!items || items.length === 0) {
        el.innerHTML = '<span class="text-muted" style="font-size:0.85rem;">None listed</span>';
        return;
    }
    el.innerHTML = items.map(item => `<span class="badge-pill ${badgeClass}">${escapeHtml(item)}</span>`).join('');
}

function renderList(containerId, items) {
    const el = document.getElementById(containerId);
    if (!items || items.length === 0) {
        el.innerHTML = '<li class="text-muted">No details provided.</li>';
        return;
    }
    el.innerHTML = items.map(item => `<li>${escapeHtml(item)}</li>`).join('');
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}
