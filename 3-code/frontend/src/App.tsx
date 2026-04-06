import { useState } from 'react'
import './App.css'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="app-layout">
      <header className="app-header">
        <h1 className="app-title">LeanDeep 6.0</h1>
        <nav className="app-nav">
          <span className="nav-label">Semantic Analysis</span>
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label={sidebarOpen ? 'Close marker library' : 'Open marker library'}
          >
            {sidebarOpen ? 'Hide Markers' : 'Show Markers'}
          </button>
        </nav>
      </header>

      <div className="app-body">
        <main className="app-main">
          <section className="analysis-area">
            <p className="placeholder-text">
              Upload or paste a dialogue to begin analysis.
            </p>
          </section>
        </main>

        {sidebarOpen && (
          <aside className="app-sidebar" aria-label="Marker Library">
            <h2 className="sidebar-title">Marker Library</h2>
            <p className="placeholder-text">Search and filter markers here.</p>
          </aside>
        )}
      </div>
    </div>
  )
}

export default App
