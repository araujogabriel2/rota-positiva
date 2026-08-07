const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'

export interface HealthResponse {
  status: 'ok'
  application: string
  api_version: string
}

export async function getApiHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`A API respondeu com o código ${response.status}.`)
  }

  return response.json() as Promise<HealthResponse>
}
