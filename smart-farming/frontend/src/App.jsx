import React, { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:5000";

function App() {
  // Basic data
  const [plots, setPlots] = useState([]);
  const [selectedPlot, setSelectedPlot] = useState("");
  const [selectedYear, setSelectedYear] = useState("2015");
  const [plotSummary, setPlotSummary] = useState(null);

  // Recommendations
  const [needsFertPlots, setNeedsFertPlots] = useState([]);
  const [postponeFertPlots, setPostponeFertPlots] = useState([]);
  const [highPestRiskPlots, setHighPestRiskPlots] = useState([]);
  const [nextCropRecs, setNextCropRecs] = useState([]);

  // UI
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ========== helpers ==========

  async function safeFetch(url, label) {
    try {
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`${label} failed (${res.status})`);
      }
      return await res.json();
    } catch (e) {
      console.error(label, "error:", e);
      setError(e.message || String(e));
      return null;
    }
  }

  // ========== initial load ==========

  useEffect(() => {
    async function init() {
      setLoading(true);
      setError("");

      // 1) load plots
      const plotsJson = await safeFetch(`${API_BASE}/api/plots`, "Load plots");
      if (plotsJson && Array.isArray(plotsJson.plots)) {
        setPlots(plotsJson.plots);
        if (!selectedPlot && plotsJson.plots.length > 0) {
          setSelectedPlot(plotsJson.plots[0]);
        }
      }

      // 2) load all recommendation endpoints in parallel
      const [
        needsF,
        postponeF,
        highPest,
        nextCrop,
      ] = await Promise.all([
        safeFetch(
          `${API_BASE}/api/recommendations/needs-fertilizer`,
          "Needs-fertilizer"
        ),
        safeFetch(
          `${API_BASE}/api/recommendations/postpone-fertilizer`,
          "Postpone-fertilizer"
        ),
        safeFetch(
          `${API_BASE}/api/recommendations/high-pest-risk`,
          "High-pest-risk"
        ),
        safeFetch(
          `${API_BASE}/api/recommendations/next-crop`,
          "Next-crop"
        ),
      ]);

      if (needsF && Array.isArray(needsF.plots)) {
        setNeedsFertPlots(needsF.plots);
      }
      if (postponeF && Array.isArray(postponeF.plots)) {
        setPostponeFertPlots(postponeF.plots);
      }
      if (highPest && Array.isArray(highPest.plots)) {
        setHighPestRiskPlots(highPest.plots);
      }
      if (nextCrop && Array.isArray(nextCrop.items)) {
        setNextCropRecs(nextCrop.items);
      }

      setLoading(false);
    }

    init();
  }, []);

  // ========== load plot/year summary when selection changes ==========

  useEffect(() => {
    if (!selectedPlot || !selectedYear) return;

    async function loadSummary() {
      setLoading(true);
      setError("");
      const url = `${API_BASE}/api/plots/${selectedPlot}/year/${selectedYear}`;
      const json = await safeFetch(url, "Plot/year summary");
      if (json && !json.error) {
        setPlotSummary(json);
      } else {
        setPlotSummary(null);
      }
      setLoading(false);
    }

    loadSummary();
  }, [selectedPlot, selectedYear]);

  // ========== derived helpers ==========

  const years = [
    "2011",
    "2012",
    "2013",
    "2014",
    "2015",
    "2016",
    "2017",
    "2018",
    "2019",
    "2020",
    "2021",
    "2022",
    "2023",
    "2024",
  ];

  function isInNeedsFert(pid) {
    return needsFertPlots.includes(pid);
  }

  function isInPostponeFert(pid) {
    return postponeFertPlots.some((p) =>
      typeof p === "string" ? p === pid : p.plot_id === pid
    );
  }

  function isInHighPest(pid) {
    return highPestRiskPlots.some((p) =>
      typeof p === "string" ? p === pid : p.plot_id === pid
    );
  }

  function getNextCropForPlotYear(pid, year) {
    return nextCropRecs.find(
      (r) => r.plot_id === pid && String(r.year) === String(year)
    );
  }

  // ========== render helpers ==========

  const RecommendationBadge = ({ active, label, color }) => {
    if (!active) return null;
    return (
      <span className={`badge badge-${color}`}>
        {label}
      </span>
    );
  };

  // ========== main render ==========

  return (
    <div className="app">
      <header className="app-header">
        <h1>Smart Farming Recommender</h1>
        <p className="subtitle">
          Ontology-driven fertilizer, pest, and crop rotation insights
        </p>
      </header>

      <main className="layout">
        {}
        <section className="panel">
          <h2>Plot &amp; Year View</h2>
          <div className="selector-row">
            <div className="field">
              <label>Plot</label>
              <select
                value={selectedPlot}
                onChange={(e) => setSelectedPlot(e.target.value)}
              >
                {plots.map((pid) => (
                  <option key={pid} value={pid}>
                    {pid}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Year</label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value)}
              >
                {years.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {loading && <div className="info">Loading…</div>}
          {error && <div className="error">Error: {error}</div>}

          {plotSummary ? (
            <div className="card">
              <h3>
                Plot {plotSummary.plot_id} – {plotSummary.year}
              </h3>
              <div className="tags">
                <span className="tag">
                  Crop: {plotSummary.crop_name || "N/A"}
                </span>
               {}
              </div>

              <div className="grid-2">
                <div>
                  <h4>Yield</h4>
                  <p className="big-number">
                    {plotSummary.yield_kg_per_ha != null
                      ? `${plotSummary.yield_kg_per_ha.toFixed(1)} kg/ha`
                      : "N/A"}
                  </p>
                </div>
                <div>
                  <h4>Soil</h4>
                  <ul className="kv-list">
                    <li>pH: {plotSummary.soil.pH ?? "N/A"}</li>
                    <li>P: {plotSummary.soil.P_mg_per_kg ?? "N/A"} mg/kg</li>
                    <li>K: {plotSummary.soil.K_mg_per_kg ?? "N/A"} mg/kg</li>
                    {}
                  </ul>
                </div>
              </div>

              <div>
                <h4>Weather</h4>
                <ul className="kv-list">
                  <li>
                    Total rainfall:{" "}
                    {plotSummary.weather.total_precip_mm ?? "N/A"} mm
                  </li>
                  <li>
                    Avg Tmax: {plotSummary.weather.avg_tmax_C ?? "N/A"} °C
                  </li>
                  <li>
                    Avg Tmin: {plotSummary.weather.avg_tmin_C ?? "N/A"} °C
                  </li>
                </ul>
              </div>

              <div className="badges-row">
                <RecommendationBadge
                  active={isInNeedsFert(plotSummary.plot_id)}
                  label="Needs fertilizer"
                  color="danger"
                />
                {}
                <RecommendationBadge
                  active={isInHighPest(plotSummary.plot_id)}
                  label="High pest risk"
                  color="accent"
                />
                {(() => {
                  const rec = getNextCropForPlotYear(
                    plotSummary.plot_id,
                    plotSummary.year
                  );
                  if (!rec) return null;
                  return (
                    <span className="badge badge-success">
                      Next crop: {rec.recommended_next_crop} (
                      {rec.recommended_next_crop_class})
                    </span>
                  );
                })()}
              </div>
            </div>
          ) : (
            <div className="info">No summary for this plot/year.</div>
          )}
        </section>

        {}
        {false && (
          <section className="panel">
            <h2>2. Recommendations Overview</h2>

            <div className="card-grid">
              {/* Needs fertilizer */}
              <div className="card">
                <h3>Needs Fertilizer</h3>
                <p className="card-desc">
                  Plots identified as nutrient-limited by low yield or low soil
                  N/P.
                </p>
                {needsFertPlots.length === 0 ? (
                  <p className="info">No plots currently flagged.</p>
                ) : (
                  <ul className="pill-list">
                    {needsFertPlots.map((pid) => (
                      <li
                        key={pid}
                        className={
                          "pill" + (pid === selectedPlot ? " pill-active" : "")
                        }
                      >
                        {pid}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Postpone fertilizer */}
              <div className="card">
                <h3>Postpone Fertilizer</h3>
                <p className="card-desc">
                  Plots with adequate soil P and very high forecast rainfall.
                </p>
                {postponeFertPlots.length === 0 ? (
                  <p className="info">No plots currently flagged.</p>
                ) : (
                  <ul className="pill-list">
                    {postponeFertPlots.map((row, idx) => {
                      const pid =
                        typeof row === "string" ? row : row.plot_id || `#${idx}`;
                      return (
                        <li
                          key={pid + idx}
                          className={
                            "pill" + (pid === selectedPlot ? " pill-active" : "")
                          }
                        >
                          {pid}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>

              {/* High pest risk */}
              <div className="card">
                <h3>High Pest Risk</h3>
                <p className="card-desc">
                  Plots where weather / yield patterns indicate elevated pest
                  pressure.
                </p>
                {highPestRiskPlots.length === 0 ? (
                  <p className="info">No plots currently flagged.</p>
                ) : (
                  <ul className="pill-list">
                    {highPestRiskPlots.map((row, idx) => {
                      const pid =
                        typeof row === "string" ? row : row.plot_id || `#${idx}`;
                      return (
                        <li
                          key={pid + idx}
                          className={
                            "pill" + (pid === selectedPlot ? " pill-active" : "")
                          }
                        >
                          {pid}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>

              {/* Next crop rotation */}
              <div className="card">
                <h3>Next Crop (Rotation)</h3>
                <p className="card-desc">
                  Suggested legume ↔ cereal rotation per plot and year.
                </p>
                {nextCropRecs.length === 0 ? (
                  <p className="info">No rotation suggestions found.</p>
                ) : (
                  <div className="table-wrapper">
                    <table className="table">
                      <thead>
                        <tr>
                          <th>Plot</th>
                          <th>Year</th>
                          <th>Current crop</th>
                          <th>Next crop</th>
                        </tr>
                      </thead>
                      <tbody>
                        {nextCropRecs.slice(0, 20).map((r, idx) => (
                          <tr key={`${r.plot_id}-${r.year}-${idx}`}>
                            <td>{r.plot_id}</td>
                            <td>{r.year}</td>
                            <td>{r.current_crop}</td>
                            <td>
                              {r.recommended_next_crop}{" "}
                              <span className="tag tag-soft">
                                {r.recommended_next_crop_class}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {nextCropRecs.length > 20 && (
                      <p className="info">
                        Showing first 20 of {nextCropRecs.length} rows.
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
