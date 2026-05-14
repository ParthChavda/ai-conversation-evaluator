const evaluateBtn = document.getElementById("evaluateBtn");
const payloadEl = document.getElementById("payload");
const errorEl = document.getElementById("error");
const turnsEl = document.getElementById("turns");
let categoryChart;

loadRegistrySummary();

evaluateBtn.addEventListener("click", async () => {
  errorEl.hidden = true;
  evaluateBtn.disabled = true;
  evaluateBtn.textContent = "Evaluating";
  try {
    const payload = JSON.parse(payloadEl.value);
    const response = await fetch("/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(JSON.stringify(body, null, 2));
    renderResult(body);
  } catch (error) {
    errorEl.textContent = error.message;
    errorEl.hidden = false;
  } finally {
    evaluateBtn.disabled = false;
    evaluateBtn.textContent = "Evaluate";
  }
});

async function loadRegistrySummary() {
  try {
    const [healthResponse, facetsResponse] = await Promise.all([fetch("/health"), fetch("/facets")]);
    const health = await healthResponse.json();
    const registry = await facetsResponse.json();
    if (!healthResponse.ok) throw new Error(JSON.stringify(health));
    if (!facetsResponse.ok) throw new Error(JSON.stringify(registry));
    renderRegistrySummary(health, registry);
  } catch (error) {
    document.getElementById("registrySource").textContent = "Facet registry unavailable";
    document.getElementById("registryModel").textContent = error.message;
  }
}

function renderRegistrySummary(health, registry) {
  const count = registry.count ?? health.enabled_facets;
  const categories = registry.categories ?? [];
  document.getElementById("registryFacetCount").textContent = count.toLocaleString();
  document.getElementById("registryBatchSize").textContent = health.facet_batch_size;
  document.getElementById("registryCategoryCount").textContent = categories.length;
  document.getElementById("registryEvaluator").textContent = health.evaluator_backend.toUpperCase();
  document.getElementById("registrySource").textContent = `${count.toLocaleString()} unique assignment facets loaded`;
  document.getElementById("registryModel").textContent = `${health.evaluator_model} · max ${health.max_facets_per_request.toLocaleString()} facets/request`;
}

function renderResult(result) {
  document.getElementById("overallScore").textContent = result.metrics.overall_score.toFixed(3);
  document.getElementById("overallConfidence").textContent = result.metrics.overall_confidence.toFixed(3);
  document.getElementById("batchCount").textContent = result.metrics.batches_executed;
  renderCharts(result.metrics);
  renderTurns(result.turns);
}

function renderCharts(metrics) {
  const categories = metrics.category_scores.map((item) => item.category);
  const scores = metrics.category_scores.map((item) => item.score);
  const confidence = metrics.category_scores.map((item) => item.confidence);
  categoryChart?.destroy();
  categoryChart = new Chart(document.getElementById("categoryChart"), {
    type: "bar",
    data: {
      labels: categories,
      datasets: [
        { label: "Normalized score", data: scores, backgroundColor: "#1d7f6e" },
        { label: "Confidence", data: confidence, backgroundColor: "#4f6f9f" },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { min: 0, max: 1 } },
    },
  });
}

function renderTurns(turns) {
  turnsEl.innerHTML = turns
    .map((turn, index) => {
      const topFacets = turn.facet_scores.slice(0, 8);
      return `
        <article class="turn">
          <h3>Turn ${index + 1} · ${turn.role} · score ${turn.aggregate_score.toFixed(3)}</h3>
          <p>${escapeHtml(turn.text)}</p>
          ${topFacets
            .map(
              (facet) => `
                <div class="facet">
                  <span title="${escapeHtml(facet.facet_id)}">${facet.facet_id}</span>
                  <div class="bar" title="${escapeHtml(`${facet.reasoning_summary} Confidence: ${facet.confidence}`)}"><div style="width:${scoreWidth(facet.score)}%"></div></div>
                  <strong title="Raw score">${facet.score}</strong>
                </div>`
            )
            .join("")}
        </article>`;
    })
    .join("");
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}

function scoreWidth(score) {
  return Math.max(0, Math.min(100, ((Number(score) - 1) / 4) * 100));
}
