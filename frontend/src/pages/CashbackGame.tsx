import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

// TODO: Implement simple game (memory/coin catching)
// On success: POST /api/cashback/activate

export default function CashbackGame() {
  const navigate = useNavigate()
  const [gameStarted, setGameStarted] = useState(false)

  const handleStart = () => {
    setGameStarted(true)
    // TODO: Implement game logic
  }

  const handleWin = async () => {
    // TODO: POST /api/cashback/activate
    navigate('/')
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Мини-игра для активации кешбека</h1>
      {!gameStarted ? (
        <button onClick={handleStart}>Начать игру</button>
      ) : (
        <div>
          <p>Игра будет реализована здесь</p>
          <button onClick={handleWin}>Завершить (демо)</button>
        </div>
      )}
    </div>
  )
}

