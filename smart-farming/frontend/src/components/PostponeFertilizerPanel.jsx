import React, { useEffect, useState } from "react";
import Loader from "./Loader";
import ErrorMessage from "./ErrorMessage";

const API_BASE = "http://127.0.0.1:5000";

function PostponeFertilizerPanel() {
  const [plots, setPlots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await fetch(
        `${API_BASE}/api/recommendations/postpone-fertilizer`
      );
      if (!res.ok) throw new Error("Failed to load recommendation");
      const data = await res.json();
      setPlots(data.plots || []);
    } catch (err) {
      setError(err.message || "Error loading data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <>
      <div className="panel-header">
        <div className="panel-title">Postpone Fertilizer</div>
        <div className="panel-subtitle">
          Plots with adequate soil P and very high rainfall forecast, where fertilizer
          may leach if applied now.
        </div>
      </div>

      <div style={{ marginBottom: "0.75rem" }}>
        <button className="button secondary" onClick={loadData} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <ErrorMessage message={error} />

      {loading && <Loader text="Loading plots..." />}

      {!loading && plots.length === 0 && !error && (
        <div className="loader">No plots currently recommended for postponement.</div>
      )}

      {plots.length > 0 && (
        <div className="grid-2">
          {plots.map((row) => (
            <div className="card" key={row.plot_id}>
              <div className="card-header">
                <span className="card-title">Plot {row.plot_id}</span>
                <span className="card-tag tag-warn">Postpone</span>
              </div>
              <div className="card-body">
                <dl>
                  <dt>Soil P (mg/kg)</dt>
                  <dd>{row.soil_P_mg_per_kg.toFixed(2)}</dd>
                  <dt>Forecast rainfall (mm)</dt>
                  <dd>{row.forecast_rainfall_mm.toFixed(1)}</dd>
                  <dt>Logic</dt>
                  <dd>
                    P ≥ 15 mg/kg AND forecast rainfall &gt; 650 mm → high
                    leaching risk.
                  </dd>
                </dl>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

export default PostponeFertilizerPanel;
