import { createClient, type Session } from '@supabase/supabase-js'
import type { AuthSession } from './api'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

const supabase =
  supabaseUrl && supabasePublishableKey
    ? createClient(supabaseUrl, supabasePublishableKey)
    : null

function toAuthSession(session: Session): AuthSession {
  return {
    access_token: session.access_token,
    refresh_token: session.refresh_token,
    expires_in: session.expires_in ?? 0,
    token_type: 'bearer',
    user: {
      id: session.user.id,
      email: session.user.email ?? 'E-mail não informado',
    },
  }
}

export function isGoogleLoginConfigured() {
  return supabase !== null
}

export async function getGoogleSession(): Promise<AuthSession | null> {
  if (!supabase) return null

  const { data, error } = await supabase.auth.getSession()
  if (error) throw error
  return data.session ? toAuthSession(data.session) : null
}

export function observeGoogleSession(
  onSessionChange: (session: AuthSession | null) => void,
) {
  if (!supabase) return () => undefined

  const { data } = supabase.auth.onAuthStateChange((_event, session) => {
    onSessionChange(session ? toAuthSession(session) : null)
  })

  return () => data.subscription.unsubscribe()
}

export async function signInWithGoogle() {
  if (!supabase) {
    throw new Error('O login com Google ainda não foi configurado neste ambiente.')
  }

  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin,
    },
  })

  if (error) throw error
}

export async function signOutFromGoogle() {
  if (!supabase) return
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}
