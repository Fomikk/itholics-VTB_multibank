import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import CashbackGame from './pages/CashbackGame'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/game" element={<CashbackGame />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

