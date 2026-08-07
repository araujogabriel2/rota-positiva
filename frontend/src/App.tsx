import { type FormEvent, useEffect, useState } from 'react'
import './App.css'
import {
  getApiHealth,
  login,
  type AuthSession,
  type HealthResponse,
} from './services/api'
import {
  getGoogleSession,
  isGoogleLoginConfigured,
  observeGoogleSession,
  signInWithGoogle,
  signOutFromGoogle,
} from './services/supabase'

type ConnectionState =
  | { status: 'loading' }
  | { status: 'online'; data: HealthResponse }
  | { status: 'offline' }

function App() {
  const [connection, setConnection] = useState<ConnectionState>({ status: 'loading' })
  const [session, setSession] = useState<AuthSession | null>(() => {
    const storedSession = sessionStorage.getItem('rota-positiva-session')
    return storedSession ? (JSON.parse(storedSession) as AuthSession) : null
  })
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    let isActive = true
    getApiHealth()
      .then((data) => {
        if (isActive) setConnection({ status: 'online', data })
      })
      .catch(() => {
        if (isActive) setConnection({ status: 'offline' })
      })
    return () => {
      isActive = false
    }
  }, [])

  useEffect(() => {
    let isActive = true

    getGoogleSession()
      .then((googleSession) => {
        if (isActive && googleSession) setSession(googleSession)
      })
      .catch(() => {
        if (isActive) setError('Não foi possível recuperar a sessão do Google.')
      })

    const stopObserving = observeGoogleSession((googleSession) => {
      if (isActive && googleSession) setSession(googleSession)
    })

    return () => {
      isActive = false
      stopObserving()
    }
  }, [])

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      const newSession = await login({ email, password })
      sessionStorage.setItem('rota-positiva-session', JSON.stringify(newSession))
      setSession(newSession)
      setPassword('')
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível entrar. Tente novamente.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleGoogleLogin() {
    setError('')
    setIsSubmitting(true)
    try {
      await signInWithGoogle()
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível entrar com o Google.',
      )
      setIsSubmitting(false)
    }
  }

  async function handleLogout() {
    try {
      await signOutFromGoogle()
    } catch {
      setError('A sessão local foi encerrada, mas o Supabase não respondeu ao logout.')
    }
    sessionStorage.removeItem('rota-positiva-session')
    setSession(null)
    setEmail('')
    setPassword('')
  }

  return (
    <main className="app-shell">
      <section className="container py-4 py-md-5">
        <header className="d-flex align-items-center justify-content-between gap-3 mb-5">
          <a className="brand" href="/" aria-label="Rota Positiva — início">
            <span className="brand-mark" aria-hidden="true">R+</span>
            <span>Rota Positiva</span>
          </a>
          <span className={`api-status api-status--${connection.status}`}>
            <span aria-hidden="true" />
            {connection.status === 'online' ? 'API conectada' : 'Verificando API'}
          </span>
        </header>

        {session ? (
          <section className="welcome-panel mx-auto" aria-labelledby="welcome-title">
            <p className="eyebrow mb-3">Sessão criada pelo Supabase</p>
            <h1 id="welcome-title">Você entrou na nova aplicação.</h1>
            <p className="lead-copy">
              Esta é a primeira área autenticada do React. Nas próximas partes, o
              FastAPI validará o token e carregará o perfil e os registros financeiros.
            </p>
            <dl className="session-details">
              <div>
                <dt>Usuário</dt>
                <dd>{session.user.email}</dd>
              </div>
              <div>
                <dt>Emissor da sessão</dt>
                <dd>Supabase Auth</dd>
              </div>
            </dl>
            <button className="btn btn-outline-light btn-lg" type="button" onClick={handleLogout}>
              Sair desta sessão
            </button>
          </section>
        ) : (
          <div className="row align-items-center g-5">
            <div className="col-lg-7">
              <p className="eyebrow mb-3">Controle financeiro para motoristas</p>
              <h1 className="display-title mb-4">
                Sua rota.<br /><span>Seu resultado.</span>
              </h1>
              <p className="lead-copy">
                Entre para acompanhar faturamento, despesas, quilômetros e lucro em um só lugar.
              </p>
            </div>

            <div className="col-lg-5">
              <form className="login-card" onSubmit={handleLogin}>
                <div className="mb-4">
                  <p className="card-label mb-2">Acesse sua conta</p>
                  <h2>Bem-vindo de volta</h2>
                </div>

                {error && <div className="alert alert-danger" role="alert">{error}</div>}

                <div className="mb-3">
                  <label className="form-label" htmlFor="email">E-mail</label>
                  <input
                    className="form-control form-control-lg"
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </div>

                <div className="mb-4">
                  <label className="form-label" htmlFor="password">Senha</label>
                  <input
                    className="form-control form-control-lg"
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    minLength={6}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                </div>

                <button className="btn btn-warning btn-lg w-100" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Entrando...' : 'Entrar'}
                </button>
                <div className="login-divider" aria-hidden="true"><span>ou</span></div>
                <button
                  className="btn btn-google btn-lg w-100"
                  type="button"
                  onClick={handleGoogleLogin}
                  disabled={isSubmitting || !isGoogleLoginConfigured()}
                >
                  <span className="google-mark" aria-hidden="true">G</span>
                  Entrar com Google
                </button>
                {!isGoogleLoginConfigured() && (
                  <p className="configuration-warning" role="status">
                    Configure o Supabase no frontend para habilitar o Google.
                  </p>
                )}
                <p className="form-note">A autenticação é processada pelo Supabase Auth.</p>
              </form>
            </div>
          </div>
        )}
      </section>
    </main>
  )
}

export default App
