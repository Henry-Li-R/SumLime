import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { supabase } from './lib/supabaseClient'

export default function Login() {
  const navigate = useNavigate()

  useEffect(() => {
    // If already signed in, leave /login
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) navigate('/', { replace: true })
    })

    // Redirect on sign-in events too
    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) navigate('/', { replace: true })
    })
    return () => sub.subscription.unsubscribe()
  }, [navigate])

  return (
    <div className="w-screen min-h-screen grid place-items-center p-6">
      <div className="w-full max-w-md">
        <Auth
          supabaseClient={supabase}
          appearance={{ theme: ThemeSupa }}
          providers={['github','google']}
          redirectTo={window.location.origin}
        />
      </div>
    </div>
  )
}