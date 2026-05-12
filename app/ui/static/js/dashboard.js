const evaluateBtn = document.getElementById("evaluateBtn");
const payloadEl = document.getElementById("payload");
const errorEl = document.getElementById("error");
const turnsEl = document.getElementById("turns");
let categoryChart;
let confidenceChart;

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
  confidenceChart?.destroy();
  categoryChart = new Chart(document.getElementById("categoryChart"), {
    type: "radar",
    data: {
      labels: categories,
      datasets: [{ label: "Category score", data: scores, borderColor: "#1d7f6e", backgroundColor: "rgba(29,127,110,0.18)" }],
    },
    options: { scales: { r: { min: 0, max: 1 } } },
  });
  confidenceChart = new Chart(document.getElementById("confidenceChart"), {
    type: "bar",
    data: {
      labels: categories,
      datasets: [{ label: "Confidence", data: confidence, backgroundColor: "#4f6f9f" }],
    },
    options: { scales: { y: { min: 0, max: 1 } } },
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
                  <span>${facet.facet_id}</span>
                  <div class="bar" title="${escapeHtml(facet.reasoning_summary)}"><div style="width:${facet.confidence * 100}%"></div></div>
                  <strong>${facet.score}</strong>
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
