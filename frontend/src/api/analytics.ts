/** API functions for analytics */
import apiClient from './client'
import type { AnalyticsSummary } from './types'

export async function getAnalyticsSummary(
  clientId: string,
  period: string = '30d'
): Promise<AnalyticsSummary> {
  const response = await apiClient.get<AnalyticsSummary>(
    `/analytics/summary?client_id=${encodeURIComponent(clientId)}&period=${period}`
  )
  return response.data
}

