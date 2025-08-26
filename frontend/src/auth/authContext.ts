import { createContext } from "react";
import type { Session, User, AuthError } from "@supabase/supabase-js";

export type AuthCtx = {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signOut: () => Promise<{ error: AuthError | null }>;
};

export const AuthContext = createContext<AuthCtx>({
  session: null,
  user: null,
  loading: true,
  // Safer default: throws if hook used outside provider
  signOut: async () => {
    throw new Error("signOut called outside of AuthProvider");
  },
});