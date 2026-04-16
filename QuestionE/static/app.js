const state = {
  page: document.body.dataset.page,
  currentPage: 1,
  pageSize: 10,
  dataset: null,
};

function getFilters() {
  return {
    year: document.getElementById("year")?.value || "",
    month: document.getElementById("month")?.value || "",
    state: document.getElementById("state")?.value || "",
    zip: document.getElementById("zip")?.value.trim() || "",
    facility: document.getElementById("facility")?.value.trim() || "",
  };
}

function queryString(extra = {}) {
  const params = new URLSearchParams();
  const filters = { ...getFilters(), ...extra };
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      params.set(key, value);
    }
  });
  return params.toString();
}

async function fetchJson(path, extra = {}) {
  const query = queryString(extra);
  const response = await fetch(`${path}?${query}`);
  return response.json();
}

function fillSelect(id, values) {
  const select = document.getElementById(id);
  if (!select) return;
  select.innerHTML = `<option value="">All</option>${values
    .map((value) => `<option value="${value}">${value}</option>`)
    .join("")}`;
}

function renderTable(targetId, rows) {
  const container = document.getElementById(targetId);
  if (!container) return;
  if (!rows.length) {
    container.innerHTML = `<p class="empty">No data for the selected filters.</p>`;
    return;
  }

  const headers = Object.keys(rows[0]);
  container.innerHTML = `
    <table>
      <thead>
        <tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr>${headers.map((header) => `<td>${row[header]}</td>`).join("")}</tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderBars(targetId, rows, labelKey, valueKey) {
  const container = document.getElementById(targetId);
  if (!container) return;
  if (!rows.length) {
    container.innerHTML = `<p class="empty">No data for the selected filters.</p>`;
    return;
  }

  const max = Math.max(...rows.map((row) => row[valueKey]));
  container.innerHTML = rows
    .map((row) => {
      const width = max === 0 ? 0 : (row[valueKey] / max) * 100;
      return `
        <div class="bar-row">
          <span class="bar-label">${row[labelKey]}</span>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
          <span class="bar-value">${Number(row[valueKey]).toFixed(3)}</span>
        </div>
      `;
    })
    .join("");
}

async function loadFilters() {
  const filters = await fetchJson("/api/filters");
  state.dataset = filters.dataset || null;
  fillSelect("year", filters.years);
  fillSelect("month", filters.months);
  fillSelect("state", filters.states);
  renderDatasetNote();
}

function renderDatasetNote() {
  const container = document.getElementById("datasetNote");
  if (!container || !state.dataset) return;

  const periodText = state.dataset.latestPeriod || "N/A";
  const singlePeriodText = state.dataset.singlePeriod
    ? "This CMS file is currently a single reporting-period snapshot, so the trend view shows one period."
    : "This CMS file contains multiple reporting periods.";

  container.innerHTML = `
    <h2>Dataset Note</h2>
    <p class="note-text">
      Source: <code>${state.dataset.sourceFile}</code>. Date field used for filtering:
      <code>${state.dataset.derivedDateField}</code>. ${state.dataset.dateRule}
      Latest loaded period: <strong>${periodText}</strong>. ${singlePeriodText}
    </p>
  `;
}

async function loadSummaryPage() {
  const summary = await fetchJson("/api/summary");
  const cards = document.getElementById("summaryCards");
  cards.innerHTML = `
    <article class="card stat"><span>Total Facilities</span><strong>${summary.total}</strong></article>
    <article class="card stat"><span>Average Mortality</span><strong>${summary.avgMortality ?? "N/A"}</strong></article>
    <article class="card stat"><span>Min Mortality</span><strong>${summary.minMortality ?? "N/A"}</strong></article>
    <article class="card stat"><span>Max Mortality</span><strong>${summary.maxMortality ?? "N/A"}</strong></article>
  `;
  renderTable("topHighest", summary.top10Highest);
  renderTable("topLowest", summary.top10Lowest);

  const table = await fetchJson("/api/table", {
    page: state.currentPage,
    pageSize: state.pageSize,
  });
  renderTable("tableContainer", table.data);
  document.getElementById("pageLabel").textContent = `Page ${table.page} of ${Math.max(
    1,
    Math.ceil(table.total / table.pageSize)
  )}`;
  document.getElementById("prevPage").disabled = table.page <= 1;
  document.getElementById("nextPage").disabled = table.page * table.pageSize >= table.total;
}

async function loadAnalysisPage() {
  const analysis = await fetchJson("/api/analysis");
  renderBars(
    "monthlyTrend",
    analysis.monthlyTrend.map((row) => ({
      period: `${row.year}-${String(row.month).padStart(2, "0")}`,
      avgMortality: row.mortality_rate,
    })),
    "period",
    "avgMortality"
  );
  renderBars("byState", analysis.byState, "state", "avgMortality");
  renderBars("byZip", analysis.byZip, "zip", "avgMortality");
  renderBars("distribution", analysis.distribution, "bucket", "count");
  renderTable("ranking", analysis.ranking);
}

async function refresh() {
  if (state.page === "summary") {
    await loadSummaryPage();
  } else {
    await loadAnalysisPage();
  }
}

function attachEvents() {
  document.getElementById("applyFilters")?.addEventListener("click", async () => {
    state.currentPage = 1;
    await refresh();
  });

  document.getElementById("resetFilters")?.addEventListener("click", async () => {
    ["year", "month", "state", "zip", "facility"].forEach((id) => {
      const element = document.getElementById(id);
      if (element) element.value = "";
    });
    state.currentPage = 1;
    await refresh();
  });

  document.getElementById("prevPage")?.addEventListener("click", async () => {
    state.currentPage = Math.max(1, state.currentPage - 1);
    await loadSummaryPage();
  });

  document.getElementById("nextPage")?.addEventListener("click", async () => {
    state.currentPage += 1;
    await loadSummaryPage();
  });

  document.getElementById("exportCsv")?.addEventListener("click", () => {
    window.location.href = `/api/export?${queryString()}`;
  });
}

async function init() {
  await loadFilters();
  attachEvents();
  await refresh();
}

init();
