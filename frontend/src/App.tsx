import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import CashbackGame from './pages/CashbackGame'
import ConnectBank from './pages/ConnectBank'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/game" element={<CashbackGame />} />
        <Route path="/connect" element={<ConnectBank />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

