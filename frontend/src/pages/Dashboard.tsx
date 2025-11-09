import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { getAnalyticsSummary } from '../api/analytics'
import { getTransactions } from '../api/transactions'
import { getLinkedAccounts } from '../api/accounts'
import type { AnalyticsSummary, Transaction, LinkedAccount } from '../api/types'
import Card from '../components/Card'
import ErrorAlert from '../components/ErrorAlert'
import LoadingSpinner from '../components/LoadingSpinner'
import TransactionsTable from '../components/TransactionsTable'

// Default client ID for demo
const DEFAULT_CLIENT_ID = 'team268-1'

// Colors for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [linkedAccounts, setLinkedAccounts] = useState<LinkedAccount[]>([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load analytics, transactions, and linked accounts in parallel
      const [analyticsData, transactionsData, linkedAccountsData] = await Promise.all([
        getAnalyticsSummary(DEFAULT_CLIENT_ID, '30d'),
        getTransactions({
          client_id: DEFAULT_CLIENT_ID,
          from_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        }),
        getLinkedAccounts(DEFAULT_CLIENT_ID).catch(() => []), // Don't fail if no linked accounts
      ])

      // Log received data for debugging
      console.log('📊 Analytics data received:', {
        net_worth: analyticsData.net_worth,
        total_accounts: analyticsData.total_accounts,
        total_spending: analyticsData.total_spending,
        spending_by_category: analyticsData.spending_by_category,
        transactions_count: transactionsData.length,
        linked_accounts_count: linkedAccountsData.length,
      })

      setAnalytics(analyticsData)
      setTransactions(transactionsData)
      setLinkedAccounts(linkedAccountsData)
    } catch (err: any) {
      let errorMessage = 'Ошибка загрузки данных'
      
      if (err?.code === 'ECONNREFUSED' || err?.message?.includes('ECONNREFUSED') || err?.message?.includes('Network Error')) {
        errorMessage = 'Backend сервер не запущен. Запустите backend на http://localhost:8000'
      } else if (err?.response?.status === 500) {
        errorMessage = err?.response?.data?.detail || 'Внутренняя ошибка сервера'
      } else if (err?.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      console.error('Failed to load dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <ErrorAlert message={error} onClose={() => setError(null)} />
          <button
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    )
  }

  // Prepare data for charts
  const categoryData = analytics
    ? Object.entries(analytics.spending_by_category).map(([name, value]) => ({
        name,
        value: Math.round(value),
      }))
    : []

  const weeklyTrendData = analytics?.weekly_trend.map((item) => ({
    week: new Date(item.week).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
    }),
    spending: Math.round(item.spending),
  })) || []

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">FinGuru Dashboard</h1>
              <p className="text-gray-600">Обзор ваших финансов</p>
            </div>
            <Link
              to="/connect"
              className="px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors"
            >
              Подключить счет
            </Link>
          </div>
        </div>

        {/* Accounts Info Banner */}
        {analytics && analytics.total_accounts > 0 ? (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-green-900 mb-1">
                  ✅ Подключено счетов: {analytics.total_accounts}
                </h3>
                <p className="text-sm text-green-700">
                  Данные успешно получены из банковских API
                  {linkedAccounts.length > 0 && (
                    <span className="ml-2">
                      ({linkedAccounts.length} вручную связанных)
                    </span>
                  )}
                </p>
              </div>
              <Link
                to="/connect"
                className="text-green-600 hover:text-green-700 text-sm font-medium"
              >
                Управление →
              </Link>
            </div>
          </div>
        ) : linkedAccounts.length > 0 ? (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-yellow-900 mb-1">
                  ⚠️ Вручную связанных счетов: {linkedAccounts.length}
                </h3>
                <p className="text-sm text-yellow-700">
                  Счета связаны, но данные ещё не получены из банковских API. 
                  Убедитесь, что банковские учетные данные настроены правильно.
                </p>
              </div>
              <Link
                to="/connect"
                className="text-yellow-600 hover:text-yellow-700 text-sm font-medium"
              >
                Управление →
              </Link>
            </div>
          </div>
        ) : (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              💡 <strong>Подключите банковские счета</strong> для отображения данных. 
              <Link to="/connect" className="text-yellow-600 hover:text-yellow-700 underline ml-1">
                Подключить сейчас →
              </Link>
            </p>
          </div>
        )}

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card
            title="Чистый капитал"
            value={analytics ? formatCurrency(analytics.net_worth) : '—'}
            subtitle={`${analytics?.total_accounts || 0} счетов`}
          />
          <Card
            title="Расходы за период"
            value={analytics ? formatCurrency(analytics.total_spending) : '—'}
            subtitle="За последние 30 дней"
          />
          <Card
            title="Активные бонусы"
            value={analytics?.top_expenses.length || 0}
            subtitle="Категории с повышенным кешбеком"
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Spending by Category Pie Chart */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Расходы по категориям</h2>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => formatCurrency(value)}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500 text-center py-8">Нет данных для отображения</p>
            )}
          </div>

          {/* Weekly Trend Line Chart */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Динамика расходов</h2>
            {weeklyTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={weeklyTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis
                    tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    formatter={(value: number) => formatCurrency(value)}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="spending"
                    stroke="#8884d8"
                    strokeWidth={2}
                    name="Расходы"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500 text-center py-8">Нет данных для отображения</p>
            )}
          </div>
        </div>

        {/* Transactions Table */}
        <div className="mb-8">
          <TransactionsTable transactions={transactions} maxRows={10} />
        </div>

        {/* Top Expenses */}
        {analytics && analytics.top_expenses.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Топ расходы</h2>
            <div className="space-y-2">
              {analytics.top_expenses.map((expense, index) => (
                <div
                  key={index}
                  className="flex justify-between items-center py-2 border-b border-gray-200 last:border-0"
                >
                  <span className="text-gray-700 capitalize">{expense.category}</span>
                  <span className="font-semibold text-red-600">
                    {formatCurrency(expense.amount)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTA Buttons */}
        <div className="text-center space-x-4">
          <Link
            to="/connect"
            className="inline-block px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors"
          >
            Подключить счет
          </Link>
          <Link
            to="/game"
            className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
          >
            Активировать кешбек
          </Link>
        </div>
      </div>
    </div>
  )
}
