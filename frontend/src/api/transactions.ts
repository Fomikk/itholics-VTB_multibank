/** API functions for transactions */
import apiClient from './client'
import type { Transaction } from './types'

export interface GetTransactionsParams {
  client_id: string
  from_date?: string
  to_date?: string
  bank?: string
}

export async function getTransactions(params: GetTransactionsParams): Promise<Transaction[]> {
  const searchParams = new URLSearchParams({ client_id: params.client_id })
  if (params.from_date) {
    searchParams.append('from_date', params.from_date)
  }
  if (params.to_date) {
    searchParams.append('to_date', params.to_date)
  }
  if (params.bank) {
    searchParams.append('bank', params.bank)
  }
  
  const response = await apiClient.get<Transaction[]>(`/transactions/aggregate?${searchParams.toString()}`)
  return response.data
}

