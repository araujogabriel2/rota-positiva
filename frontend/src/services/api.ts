const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'

export interface HealthResponse {
  status: 'ok'
  application: string
  api_version: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthSession {
  access_token: string
  refresh_token: string
  expires_in: number
  token_type: 'bearer'
  user: {
    id: string
    email: string
  }
}

interface ApiErrorResponse {
  detail?: string
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

export async function login(credentials: LoginCredentials): Promise<AuthSession> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  })

  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as ApiErrorResponse
    throw new Error(error.detail ?? 'Não foi possível entrar. Tente novamente.')
  }

  return response.json() as Promise<AuthSession>
}
