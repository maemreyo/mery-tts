import { createContext, useCallback, useContext, useState } from "react";

export interface SmokeRecord {
  voiceId: string;
  voiceLabel: string;
  ok: boolean;
  timestamp: string;
}

export interface InstallRecord {
  voiceId: string;
  voiceLabel: string;
  status: "succeeded" | "failed" | "cancelled";
  timestamp: string;
}

export interface SessionActivityState {
  lastSmoke: SmokeRecord | null;
  lastInstall: InstallRecord | null;
  recordSmoke: (record: SmokeRecord) => void;
  recordInstall: (record: InstallRecord) => void;
}

export const SessionActivityContext =
  createContext<SessionActivityState | null>(null);

export function SessionActivityProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [lastSmoke, setLastSmoke] = useState<SmokeRecord | null>(null);
  const [lastInstall, setLastInstall] = useState<InstallRecord | null>(null);

  const recordSmoke = useCallback((record: SmokeRecord) => {
    setLastSmoke(record);
  }, []);

  const recordInstall = useCallback((record: InstallRecord) => {
    setLastInstall(record);
  }, []);

  return (
    <SessionActivityContext.Provider
      value={{ lastSmoke, lastInstall, recordSmoke, recordInstall }}
    >
      {children}
    </SessionActivityContext.Provider>
  );
}

export function useSessionActivity(): SessionActivityState {
  const ctx = useContext(SessionActivityContext);
  if (ctx === null) {
    throw new Error(
      "useSessionActivity must be used within a SessionActivityProvider",
    );
  }
  return ctx;
}
