import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

// TODO: Implement dashboard with:
// - Net Worth card
// - Recent transactions
// - Category spending chart (Pie)
// - Spending trend chart (Line)
// - CTA button to cashback game

export default function Dashboard() {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: Fetch data from /api/analytics/summary
    setLoading(false)
  }, [])

  if (loading) {
    return <div>Загрузка...</div>
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>FinGuru Dashboard</h1>
      <p>Дашборд будет реализован здесь</p>
      <Link to="/game">
        <button>Активировать кешбек</button>
      </Link>
    </div>
  )
}

