import React, { useEffect, useState } from "react";
import Loader from "./Loader";
import ErrorMessage from "./ErrorMessage";

const API_BASE = "http://127.0.0.1:5000";

function NextCropPanel() {
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await fetch(`${API_BASE}/api/recommendations/next-crop`);
      if (!res.ok) throw new Error("Failed to load recommendation");
      const data = await res.json();
      setRecs(data.recommendations || []);
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
        <div className="panel-title">Next Crop Rotation</div>
        <div className="panel-subtitle">
          Rotation rule: maize → soybean (legume), soybean → maize (cereal).
        </div>
      </div>

      <div style={{ marginBottom: "0.75rem" }}>
        <button className="button secondary" onClick={loadData} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <ErrorMessage message={error} />

      {loading && <Loader text="Loading recommendations..." />}

      {!loading && recs.length === 0 && !error && (
        <div className="loader">
          No rotation recommendations found (check yield records in the KG).
        </div>
      )}

      {recs.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Plot</th>
              <th>Year</th>
              <th>Current crop</th>
              <th>Recommended next crop</th>
              <th>Next crop class</th>
            </tr>
          </thead>
          <tbody>
            {recs.map((r, idx) => (
              <tr key={`${r.plot_id}-${r.year}-${idx}`}>
                <td>{r.plot_id}</td>
                <td>{r.year}</td>
                <td>{r.current_crop}</td>
                <td>{r.recommended_next_crop}</td>
                <td>{r.recommended_next_crop_class}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}

export default NextCropPanel;
