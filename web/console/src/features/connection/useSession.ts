import {
  clearSession,
  persistSession,
  readInitialSession,
} from "@shared/auth/session";
import { useCallback, useEffect, useState } from "react";
import type { SessionValues } from "./types";

export function useSession() {
  const [session, setSession] = useState<SessionValues>(readInitialSession);

  useEffect(() => {
    persistSession(session);
  }, [session]);

  const applyToken = useCallback((token: string, remember: boolean) => {
    setSession({ token, remember });
  }, []);

  const logout = useCallback(() => {
    setSession(clearSession());
  }, []);

  return { session, applyToken, logout };
}
