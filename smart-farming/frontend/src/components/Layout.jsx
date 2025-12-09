import React from "react";

function Layout({ tabs, activeTab, onTabChange, children }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Smart Farming Recommender</h1>
          <span>Ontology + rules powered decision support</span>
        </div>
      </header>

      <main className="app-main">
        <div className="tabs">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`tab-button ${
                activeTab === t.id ? "active" : ""
              }`.trim()}
              onClick={() => onTabChange(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="panel">{children}</div>
      </main>
    </div>
  );
}

export default Layout;
