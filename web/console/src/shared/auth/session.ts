const TOKEN_STORAGE_KEY = "mery.console.authToken";

interface ConsoleSession {
  token: string;
  remember: boolean;
}

export function readInitialSession(): ConsoleSession {
  return {
    token: globalThis.localStorage?.getItem(TOKEN_STORAGE_KEY) ?? "",
    remember: Boolean(globalThis.localStorage?.getItem(TOKEN_STORAGE_KEY)),
  };
}

export function persistSession(session: ConsoleSession): void {
  if (!session.remember || session.token.length === 0) {
    globalThis.localStorage?.removeItem(TOKEN_STORAGE_KEY);
    return;
  }

  globalThis.localStorage?.setItem(TOKEN_STORAGE_KEY, session.token);
}

export function clearSession(): ConsoleSession {
  globalThis.localStorage?.removeItem(TOKEN_STORAGE_KEY);
  return { token: "", remember: false };
}
