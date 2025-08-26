import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from './supabaseClient'
import type { Session, User, AuthError } from '@supabase/supabase-js'

type AuthCtx = {
  session: Session | null
  user: User | null
  loading: boolean
  signOut: () => Promise<{ error: AuthError | null }>
}
const Ctx = createContext<AuthCtx>({
  session: null,
  user: null,
  loading: true,
  signOut: async (): Promise<{ error: AuthError | null }> => ({ error: null })
});
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session ?? null); setLoading(false)
    })
    const { data: sub } = supabase.auth.onAuthStateChange((_e, s) => setSession(s))
    return () => { sub.subscription.unsubscribe() }
  }, [])

  const value: AuthCtx = {
    session,
    user: session?.user ?? null,
    loading,
    signOut: () => supabase.auth.signOut(),
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}