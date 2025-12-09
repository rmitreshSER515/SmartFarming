import React, { useEffect, useState } from "react";
import Loader from "./Loader";
import ErrorMessage from "./ErrorMessage";

const API_BASE = "http://127.0.0.1:5000";

function NeedsFertilizerPanel() {
  const [plots, setPlots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await fetch(
        `${API_BASE}/api/recommendations/needs-fertilizer`
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
        <div className="panel-title">Plots Needing Fertilizer</div>
        <div className="panel-subtitle">
          Based on low yield or low soil P/N from the knowledge graph.
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
        <div className="loader">No plots currently flagged as needing fertilizer.</div>
      )}

      {plots.length > 0 && (
        <div className="grid-2">
          {plots.map((pid) => (
            <div className="card" key={pid}>
              <div className="card-header">
                <span className="card-title">Plot {pid}</span>
                <span className="card-tag tag-critical">Needs fertilizer</span>
              </div>
              <div className="card-body">
                <p>
                  This plot is below threshold for yield or soil nutrients
                  (P/N). The backend rule:
                </p>
                <ul style={{ marginLeft: "1rem", marginTop: "0.4rem" }}>
                  <li>Yield &lt; 2000 kg/ha OR</li>
                  <li>Soil P &lt; 15 mg/kg OR</li>
                  <li>Soil N &lt; 10 mg/kg</li>
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

export default NeedsFertilizerPanel;
