/** API types for FinGuru */

export interface Account {
  account_id: string
  bank: string
  currency: string
  account_type: string
  nickname?: string
  servicer?: Record<string, unknown>
}

export interface Transaction {
  transaction_id: string
  account_id: string
  amount: string
  currency: string
  booking_date: string
  description?: string
  mcc?: string
}

export interface AnalyticsSummary {
  net_worth: number
  total_accounts: number
  total_spending: number
  spending_by_category: Record<string, number>
  top_expenses: Array<{
    category: string
    amount: number
  }>
  weekly_trend: Array<{
    week: string
    spending: number
  }>
  period_days: number
}

export interface CashbackBonus {
  category: string
  bonus_percent: number
  valid_until: string
  activated_at: string
}

export interface CashbackActivateRequest {
  client_id: string
  category: string
  bonus_percent: number
  valid_until?: string
}

export interface CashbackActivateResponse {
  activated: boolean
  category: string
  bonus_percent: number
  valid_until: string
  activated_at: string
}

