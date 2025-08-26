// src/auth/useAuth.ts
import { useContext } from "react";
import { AuthContext } from "./authContext";

export const useAuth = () => useContext(AuthContext);