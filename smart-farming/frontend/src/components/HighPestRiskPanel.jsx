import React, { useEffect, useState } from "react";
import Loader from "./Loader";
import ErrorMessage from "./ErrorMessage";

const API_BASE = "http://127.0.0.1:5000";

function HighPestRiskPanel() {
  const [plots, setPlots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await fetch(
        `${API_BASE}/api/recommendations/high-pest-risk`
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
        <div className="panel-title">High Pest Risk Plots</div>
        <div className="panel-subtitle">
          Maize plots with high rainfall and relatively low yield, indicating possible
          pest or disease pressure.
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
        <div className="loader">No plots currently flagged as high pest risk.</div>
      )}

      {plots.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Plot</th>
              <th>Crop</th>
              <th>Forecast rainfall (mm)</th>
              <th>Yield (kg/ha)</th>
            </tr>
          </thead>
          <tbody>
            {plots.map((row) => (
              <tr key={row.plot_id}>
                <td>{row.plot_id}</td>
                <td>{row.crop_name}</td>
                <td>{row.forecast_rainfall_mm.toFixed(1)}</td>
                <td>{row.yield_kg_per_ha.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}

export default HighPestRiskPanel;
