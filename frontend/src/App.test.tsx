import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('App', () => {
  it('mostra que o React conseguiu consultar o FastAPI', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          status: 'ok',
          application: 'Rota Positiva API',
          api_version: 'v1',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    render(<App />)

    expect(screen.getByText('Verificando a API...')).toBeInTheDocument()
    expect(await screen.findByText('API conectada')).toBeInTheDocument()
    expect(screen.getByText('Rota Positiva API · v1')).toBeInTheDocument()
  })

  it('orienta o usuário quando o backend está desligado', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Falha de conexão'))

    render(<App />)

    expect(await screen.findByText('API ainda não encontrada')).toBeInTheDocument()
    expect(screen.getByText('Falha de conexão')).toBeInTheDocument()
  })
})
