import { useEffect, useState } from 'react'
import './App.css'
import { getApiHealth, type HealthResponse } from './services/api'

type ConnectionState =
  | { status: 'loading' }
  | { status: 'online'; data: HealthResponse }
  | { status: 'offline'; message: string }

function App() {
  const [connection, setConnection] = useState<ConnectionState>({ status: 'loading' })

  useEffect(() => {
    let isActive = true

    getApiHealth()
      .then((data) => {
        if (isActive) setConnection({ status: 'online', data })
      })
      .catch((error: unknown) => {
        if (!isActive) return
        const message = error instanceof Error ? error.message : 'Não foi possível consultar a API.'
        setConnection({ status: 'offline', message })
      })

    return () => {
      isActive = false
    }
  }, [])

  return (
    <main className="app-shell">
      <section className="container py-4 py-md-5">
        <header className="d-flex align-items-center justify-content-between gap-3 mb-5">
          <a className="brand" href="/" aria-label="Rota Positiva — início">
            <span className="brand-mark" aria-hidden="true">R+</span>
            <span>Rota Positiva</span>
          </a>
          <span className="phase-badge">Nova arquitetura · Fase 1</span>
        </header>

        <div className="row align-items-center g-5">
          <div className="col-lg-7">
            <p className="eyebrow mb-3">Base técnica em funcionamento</p>
            <h1 className="display-title mb-4">
              Um novo motor para sua <span>vida financeira.</span>
            </h1>
            <p className="lead-copy mb-4">
              O React já está preparado para ser a nova interface do Rota Positiva.
              Nesta etapa, validamos a comunicação segura com a API FastAPI.
            </p>
            <div className="d-flex flex-wrap gap-2" aria-label="Tecnologias da nova arquitetura">
              <span className="tech-pill">React + TypeScript</span>
              <span className="tech-pill">FastAPI</span>
              <span className="tech-pill">API versionada</span>
            </div>
          </div>

          <div className="col-lg-5">
            <article className="connection-card" aria-live="polite">
              <p className="card-label">Conexão com o backend</p>
              {connection.status === 'loading' && (
                <div className="status-row">
                  <span className="spinner-border spinner-border-sm text-warning" aria-hidden="true" />
                  <div>
                    <strong>Verificando a API...</strong>
                    <p>Aguarde enquanto o frontend procura o FastAPI.</p>
                  </div>
                </div>
              )}

              {connection.status === 'online' && (
                <div className="status-row">
                  <span className="status-dot status-dot--online" aria-hidden="true" />
                  <div>
                    <strong>API conectada</strong>
                    <p>{connection.data.application} · {connection.data.api_version}</p>
                  </div>
                </div>
              )}

              {connection.status === 'offline' && (
                <div className="status-row">
                  <span className="status-dot status-dot--offline" aria-hidden="true" />
                  <div>
                    <strong>API ainda não encontrada</strong>
                    <p>{connection.message}</p>
                    <small>Inicie o FastAPI na porta 8000 e atualize esta página.</small>
                  </div>
                </div>
              )}

              <hr />
              <dl className="connection-details">
                <div>
                  <dt>Frontend</dt>
                  <dd>React</dd>
                </div>
                <div>
                  <dt>Backend</dt>
                  <dd>FastAPI</dd>
                </div>
                <div>
                  <dt>Endpoint</dt>
                  <dd>/api/v1/health</dd>
                </div>
              </dl>
            </article>
          </div>
        </div>
      </section>
    </main>
  )
}

export default App
