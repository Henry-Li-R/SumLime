// src/auth/AuthProvider.tsx
import { useEffect, useState, type ReactNode } from "react";
import { supabase } from "../lib/supabaseClient";
import type { Session } from "@supabase/supabase-js";
import { AuthContext, type AuthCtx } from "./authContext";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // initial session fetch
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session ?? null);
      setLoading(false);
    });

    // subscribe to auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const value: AuthCtx = {
    session,
    user: session?.user ?? null,
    loading,
    signOut: () => supabase.auth.signOut(), // returns Promise<{ error: AuthError | null }>
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}