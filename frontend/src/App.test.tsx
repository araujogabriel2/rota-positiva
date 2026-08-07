import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const googleAuth = vi.hoisted(() => ({
  getSession: vi.fn().mockResolvedValue(null),
  observeSession: vi.fn().mockReturnValue(() => undefined),
  signIn: vi.fn().mockResolvedValue(undefined),
  signOut: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('./services/supabase', () => ({
  getGoogleSession: googleAuth.getSession,
  isGoogleLoginConfigured: () => true,
  observeGoogleSession: googleAuth.observeSession,
  signInWithGoogle: googleAuth.signIn,
  signOutFromGoogle: googleAuth.signOut,
}))

beforeEach(() => {
  sessionStorage.clear()
  vi.clearAllMocks()
  googleAuth.getSession.mockResolvedValue(null)
  googleAuth.observeSession.mockReturnValue(() => undefined)
  googleAuth.signIn.mockResolvedValue(undefined)
  googleAuth.signOut.mockResolvedValue(undefined)
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('App', () => {
  it('exibe o formulário de login e o estado da API', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({ status: 'ok', application: 'Rota Positiva API', api_version: 'v1' }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    render(<App />)

    expect(screen.getByRole('heading', { name: 'Bem-vindo de volta' })).toBeInTheDocument()
    expect(await screen.findByText('API conectada')).toBeInTheDocument()
  })

  it('entra e mostra a sessão emitida pelo Supabase', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ status: 'ok', application: 'Rota Positiva API', api_version: 'v1' }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          access_token: 'access-token',
          refresh_token: 'refresh-token',
          expires_in: 3600,
          token_type: 'bearer',
          user: { id: 'user-id', email: 'motorista@example.com' },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    render(<App />)
    fireEvent.change(screen.getByLabelText('E-mail'), { target: { value: 'motorista@example.com' } })
    fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'senha-segura' } })
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('Você entrou na nova aplicação.')).toBeInTheDocument()
    expect(screen.getByText('motorista@example.com')).toBeInTheDocument()
    await waitFor(() => expect(sessionStorage.getItem('rota-positiva-session')).not.toBeNull())
  })

  it('mostra a mensagem devolvida pelo backend quando o login falha', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ status: 'ok', application: 'Rota Positiva API', api_version: 'v1' }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: 'E-mail ou senha incorretos.' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    render(<App />)
    fireEvent.change(screen.getByLabelText('E-mail'), { target: { value: 'motorista@example.com' } })
    fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'senha-errada' } })
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha incorretos.')
  })

  it('inicia o login com Google pelo Supabase', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({ status: 'ok', application: 'Rota Positiva API', api_version: 'v1' }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )

    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Entrar com Google' }))

    await waitFor(() => expect(googleAuth.signIn).toHaveBeenCalledOnce())
  })
})
