import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MobileLayout from './layouts/MobileLayout'
import HomeView from './views/HomeView'
import SimpleMapView from './views/SimpleMapView'
import VoiceChatView from './views/VoiceChatView'
import ResultsView from './views/ResultsView'
import HistoryView from './views/HistoryView'

function App() {
  const [plotData, setPlotData] = useState({
    lat: 12.5218,
    lon: 76.8951,
    area_hectares: 1.94,
    district: "Mandya District"
  })
  const [results, setResults] = useState(null)

  return (
    <BrowserRouter>
      <MobileLayout>
        <Routes>
          <Route path="/" element={<HomeView />} />
          <Route path="/discover" element={<SimpleMapView />} />
          <Route path="/map" element={<SimpleMapView />} />
          <Route path="/assistant" element={<VoiceChatView setResults={setResults} />} />
          <Route path="/impact" element={<ResultsView results={results} />} />
          <Route path="/history" element={<HistoryView />} />
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MobileLayout>
    </BrowserRouter>
  )
}

export default App
