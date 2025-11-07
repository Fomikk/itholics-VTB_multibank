/** API functions for accounts */
import apiClient from './client'
import type { Account } from './types'

export async function getAccounts(clientId: string, bank?: string): Promise<Account[]> {
  const params = new URLSearchParams({ client_id: clientId })
  if (bank) {
    params.append('bank', bank)
  }
  
  const response = await apiClient.get<Account[]>(`/accounts/aggregate?${params.toString()}`)
  return response.data
}

