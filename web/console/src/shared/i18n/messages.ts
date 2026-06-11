const messages = {
  appTitle: "Mery Console",
  appDescription:
    "Local-first TTS control plane. User Mode is recovery-focused; Developer Mode remains opt-in.",
  bearerToken: "Bearer token",
  rememberDevice: "Remember on this device",
  logout: "Log out",
  voicesHeading: "Voices",
  localeFilter: "Locale filter",
  searchVoices: "Search voices",
  sortVoices: "Sort voices",
  installVoice: "Install voice",
  loadingVoices: "Loading voices...",
  enterToken: "Enter a token to load voices.",
  noVoices: "No voices available.",
  loadVoicesError:
    "Could not load voices. Check the bearer token and local server status.",
  installQueued: "Install queued.",
  installRunning: "Install running.",
  installSucceeded: "Install succeeded.",
  installFailed: "Install failed.",
} as const;

type MessageKey = keyof typeof messages;

export function t(key: MessageKey): string {
  return messages[key];
}
