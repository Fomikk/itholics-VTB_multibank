/** API functions for accounts */
import apiClient from './client'
import type { Account, LinkedAccount } from './types'

export async function getAccounts(clientId: string, bank?: string): Promise<Account[]> {
  const params = new URLSearchParams({ client_id: clientId })
  if (bank) {
    params.append('bank', bank)
  }
  
  const response = await apiClient.get<Account[]>(`/accounts/aggregate?${params.toString()}`)
  return response.data
}

export interface LinkAccountRequest {
  bank: string
  account_number: string
  account_id?: string
  nickname?: string
}

export async function linkAccount(
  clientId: string,
  request: LinkAccountRequest
): Promise<LinkedAccount> {
  const params = new URLSearchParams({ client_id: clientId })
  const response = await apiClient.post<LinkedAccount>(
    `/accounts/link?${params.toString()}`,
    request
  )
  return response.data
}

export async function getLinkedAccounts(clientId: string): Promise<LinkedAccount[]> {
  const params = new URLSearchParams({ client_id: clientId })
  const response = await apiClient.get<LinkedAccount[]>(
    `/accounts/linked?${params.toString()}`
  )
  return response.data
}

export async function unlinkAccount(clientId: string, accountId: string): Promise<void> {
  const params = new URLSearchParams({ client_id: clientId })
  await apiClient.delete(`/accounts/link/${accountId}?${params.toString()}`)
}

