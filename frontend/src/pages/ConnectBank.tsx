import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { linkAccount, getLinkedAccounts, unlinkAccount } from '../api/accounts'
import type { LinkedAccount } from '../api/types'
import ErrorAlert from '../components/ErrorAlert'
import LoadingSpinner from '../components/LoadingSpinner'

const DEFAULT_CLIENT_ID = 'team268-1'

const BANKS = [
  { code: 'vbank', name: 'VBank' },
  { code: 'abank', name: 'ABank' },
  { code: 'sbank', name: 'SBank' },
]

export default function ConnectBank() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [loadingAccounts, setLoadingAccounts] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [linkedAccounts, setLinkedAccounts] = useState<LinkedAccount[]>([])
  
  // Form state
  const [bank, setBank] = useState('vbank')
  const [accountNumber, setAccountNumber] = useState('')
  const [nickname, setNickname] = useState('')

  useEffect(() => {
    loadLinkedAccounts()
  }, [])

  const loadLinkedAccounts = async () => {
    try {
      setLoadingAccounts(true)
      const accounts = await getLinkedAccounts(DEFAULT_CLIENT_ID)
      setLinkedAccounts(accounts)
    } catch (err: any) {
      console.error('Failed to load linked accounts:', err)
    } finally {
      setLoadingAccounts(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!accountNumber.trim()) {
      setError('Введите номер счета')
      return
    }

    try {
      setLoading(true)
      setError(null)

      await linkAccount(DEFAULT_CLIENT_ID, {
        bank,
        account_number: accountNumber.trim(),
        nickname: nickname.trim() || undefined,
      })

      // Reset form
      setAccountNumber('')
      setNickname('')
      
      // Reload accounts
      await loadLinkedAccounts()
      
      // Show success message
      alert('Счет успешно подключен!')
    } catch (err: any) {
      let errorMessage = 'Ошибка подключения счета'
      
      if (err?.response?.status === 400) {
        errorMessage = err?.response?.data?.detail || 'Неверные данные'
      } else if (err?.response?.status === 500) {
        errorMessage = err?.response?.data?.detail || 'Ошибка сервера'
      } else if (err?.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleUnlink = async (accountId: string) => {
    if (!confirm('Вы уверены, что хотите отключить этот счет?')) {
      return
    }

    try {
      await unlinkAccount(DEFAULT_CLIENT_ID, accountId)
      await loadLinkedAccounts()
      alert('Счет успешно отключен')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Ошибка отключения счета')
    }
  }

  if (loadingAccounts) {
    return <LoadingSpinner />
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="mb-4 text-blue-600 hover:text-blue-700"
          >
            ← Назад к Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Подключение банковских счетов</h1>
          <p className="text-gray-600">Подключите свои счета из разных банков для агрегации данных</p>
        </div>

        {error && (
          <div className="mb-6">
            <ErrorAlert message={error} onClose={() => setError(null)} />
          </div>
        )}

        {/* Connect Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Подключить новый счет</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="bank" className="block text-sm font-medium text-gray-700 mb-2">
                Банк
              </label>
              <select
                id="bank"
                value={bank}
                onChange={(e) => setBank(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {BANKS.map((b) => (
                  <option key={b.code} value={b.code}>
                    {b.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="accountNumber" className="block text-sm font-medium text-gray-700 mb-2">
                Номер счета *
              </label>
              <input
                type="text"
                id="accountNumber"
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value)}
                placeholder="Введите номер счета или идентификатор"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                Введите номер счета, который вы хотите подключить
              </p>
            </div>

            <div>
              <label htmlFor="nickname" className="block text-sm font-medium text-gray-700 mb-2">
                Название (необязательно)
              </label>
              <input
                type="text"
                id="nickname"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                placeholder="Например: Основной счет"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Подключение...' : 'Подключить счет'}
            </button>
          </form>
        </div>

        {/* Linked Accounts List */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Подключенные счета</h2>
          
          {linkedAccounts.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              Нет подключенных счетов. Подключите счет выше.
            </p>
          ) : (
            <div className="space-y-4">
              {linkedAccounts.map((account) => (
                <div
                  key={account.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-semibold">
                          {account.bank.toUpperCase().charAt(0)}
                        </span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {account.nickname}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {account.bank.toUpperCase()} • {account.account_number}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          Подключен: {new Date(account.linked_at).toLocaleDateString('ru-RU')}
                        </p>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleUnlink(account.id)}
                    className="px-4 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
                  >
                    Отключить
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

