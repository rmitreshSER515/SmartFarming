import React, { useEffect, useState } from "react";
import Loader from "./Loader";
import ErrorMessage from "./ErrorMessage";

const API_BASE = "http://127.0.0.1:5000";

function PlotOverview() {
  const [plots, setPlots] = useState([]);
  const [selectedPlot, setSelectedPlot] = useState("");
  const [year, setYear] = useState("2015");
  const [summary, setSummary] = useState(null);
  const [loadingPlots, setLoadingPlots] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [error, setError] = useState("");

  // Load plots list
  useEffect(() => {
    const loadPlots = async () => {
      try {
        setLoadingPlots(true);
        setError("");
        const res = await fetch(`${API_BASE}/api/plots`);
        if (!res.ok) throw new Error("Failed to load plots");
        const data = await res.json();
        setPlots(data.plots || []);
        if (data.plots && data.plots.length > 0) {
          setSelectedPlot(data.plots[0]);
        }
      } catch (err) {
        setError(err.message || "Error loading plots");
      } finally {
        setLoadingPlots(false);
      }
    };

    loadPlots();
  }, []);

  const loadSummary = async () => {
    if (!selectedPlot || !year) return;
    try {
      setLoadingSummary(true);
      setError("");
      setSummary(null);
      const res = await fetch(
        `${API_BASE}/api/plots/${encodeURIComponent(
          selectedPlot
        )}/year/${encodeURIComponent(year)}`
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Failed to load plot summary");
      }
      const data = await res.json();
      setSummary(data);
    } catch (err) {
      setError(err.message || "Error loading summary");
    } finally {
      setLoadingSummary(false);
    }
  };

  return (
    <>
      <div className="panel-header">
        <div className="panel-title">Plot Overview</div>
        <div className="panel-subtitle">
          Explore soil, yield and weather history for a specific plot &amp; year.
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>Plot</label>
          {loadingPlots ? (
            <Loader text="Loading plots..." />
          ) : (
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
          )}
        </div>

        <div className="form-group">
          <label>Year</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            min="2011"
            max="2024"
          />
        </div>

        <div className="form-group" style={{ alignSelf: "flex-end" }}>
          <button
            className="button"
            onClick={loadSummary}
            disabled={!selectedPlot || !year || loadingSummary}
          >
            {loadingSummary ? "Loading..." : "Load Summary"}
          </button>
        </div>
      </div>

      <ErrorMessage message={error} />

      {summary && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header">
              <span className="card-title">Yield</span>
              <span className="card-tag tag-info">kg/ha</span>
            </div>
            <div className="card-body">
              <dl>
                <dt>Plot</dt>
                <dd>{summary.plot_id}</dd>
                <dt>Year</dt>
                <dd>{summary.year}</dd>
                <dt>Yield</dt>
                <dd>
                  {summary.yield_kg_per_ha != null
                    ? summary.yield_kg_per_ha.toFixed(1)
                    : "–"}
                </dd>
                <dt>Crop</dt>
                <dd>{summary.crop_name || "Unknown"}</dd>
                <dt>Treatment</dt>
                <dd>{summary.treatment || "–"}</dd>
              </dl>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Soil</span>
              <span className="card-tag tag-info">Nutrients</span>
            </div>
            <div className="card-body">
              <dl>
                <dt>pH</dt>
                <dd>{summary.soil?.pH ?? "–"}</dd>
                <dt>P (mg/kg)</dt>
                <dd>{summary.soil?.P_mg_per_kg ?? "–"}</dd>
                <dt>N (mg/kg)</dt>
                <dd>
                  {/* N not in summary dict, just leave out or set "–" */}
                  –
                </dd>
                <dt>K (mg/kg)</dt>
                <dd>{summary.soil?.K_mg_per_kg ?? "–"}</dd>
                <dt>CEC</dt>
                <dd>{summary.soil?.CEC ?? "–"}</dd>
                <dt>OM (%)</dt>
                <dd>{summary.soil?.OM_pct ?? "–"}</dd>
              </dl>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Weather</span>
              <span className="card-tag tag-info">Seasonal</span>
            </div>
            <div className="card-body">
              <dl>
                <dt>Rainfall (mm)</dt>
                <dd>{summary.weather?.total_precip_mm ?? "–"}</dd>
                <dt>Avg Tmax (°C)</dt>
                <dd>{summary.weather?.avg_tmax_C ?? "–"}</dd>
                <dt>Avg Tmin (°C)</dt>
                <dd>{summary.weather?.avg_tmin_C ?? "–"}</dd>
              </dl>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default PlotOverview;
