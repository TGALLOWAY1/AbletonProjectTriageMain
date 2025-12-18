import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useState } from 'react'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import ScanPage from './pages/ScanPage'
import TriagePage from './pages/TriagePage'
import HygienePage from './pages/HygienePage'
import MigrationPage from './pages/MigrationPage'
import StudioPage from './pages/StudioPage'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden">
        <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
        <main className={`flex-1 overflow-y-auto transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
          <div className="p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/scan" element={<ScanPage />} />
              <Route path="/triage" element={<TriagePage />} />
              <Route path="/hygiene" element={<HygienePage />} />
              <Route path="/migration" element={<MigrationPage />} />
              <Route path="/studio" element={<StudioPage />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App

