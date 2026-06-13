import type { ConsoleSection } from "@features/app-shell/routes";
import type { ConnectionStatus } from "@features/connection/types";
import type { HealthResponse } from "@shared/api/meryApi";
import type { VoiceViewModel } from "@shared/api/voiceViewModels";

export type OverviewActionTarget = ConsoleSection | "connect";

export interface OverviewAction {
  label: string;
  target: OverviewActionTarget;
  description?: string;
}

export interface StatusTile {
  label: string;
  value: string;
  level: "ok" | "warn" | "error" | "neutral";
}

export interface OverviewViewModel {
  headline: string;
  description: string;
  primaryAction: OverviewAction;
  secondaryActions: OverviewAction[];
  statusTiles: StatusTile[];
}

export function deriveOverviewViewModel(params: {
  connectionStatus: ConnectionStatus;
  health: HealthResponse | null;
  healthError: boolean;
  voices: VoiceViewModel[] | null;
  isHealthLoading: boolean;
  isVoicesLoading: boolean;
}): OverviewViewModel {
  const {
    connectionStatus,
    health,
    healthError,
    voices,
    isHealthLoading,
    isVoicesLoading,
  } = params;

  const connected = connectionStatus === "connected";
  const checking = connectionStatus === "checking";

  // Status tiles — always 3
  const connectionTile: StatusTile = {
    label: "Connection",
    value: connected ? "Connected" : checking ? "Checking…" : "Disconnected",
    level: connected ? "ok" : checking ? "neutral" : "error",
  };

  const serverTile: StatusTile = {
    label: "Server",
    value: health?.health_status ?? "Unknown",
    level: health?.ready ? "ok" : healthError ? "error" : "warn",
  };

  const voicesTile: StatusTile = {
    label: "Voices",
    value: isVoicesLoading
      ? "Loading…"
      : voices?.length
        ? `${voices.length} available`
        : "None installed",
    level: voices?.length ? "ok" : "warn",
  };

  const statusTiles: StatusTile[] = [connectionTile, serverTile, voicesTile];

  // Decision logic
  if (connectionStatus === "disconnected") {
    return {
      headline: "Connect to Mery",
      description: "Enter a bearer token to continue.",
      primaryAction: { label: "Connect", target: "connect" },
      secondaryActions: [],
      statusTiles,
    };
  }

  if (checking) {
    return {
      headline: "Connecting…",
      description: "Verifying token and server…",
      primaryAction: { label: "View Health", target: "health" },
      secondaryActions: [],
      statusTiles,
    };
  }

  if (connected && healthError) {
    return {
      headline: "Cannot reach Mery",
      description: "The server is not responding.",
      primaryAction: { label: "Check Health", target: "health" },
      secondaryActions: [],
      statusTiles,
    };
  }

  if (connected && health?.ready === false) {
    return {
      headline: "Server not ready",
      description: "Mery is running but not ready.",
      primaryAction: { label: "Check Health", target: "health" },
      secondaryActions: [{ label: "Developer Mode", target: "developer" }],
      statusTiles,
    };
  }

  if (connected && health?.ready && !voices?.length) {
    return {
      headline: "No voices installed",
      description: "Install a voice model to start.",
      primaryAction: { label: "Browse Voices", target: "voices" },
      secondaryActions: [],
      statusTiles,
    };
  }

  // connected + ready + voices available
  return {
    headline: "Mery is ready",
    description: "Everything looks good. Run a smoke test or browse voices.",
    primaryAction: { label: "Run smoke test", target: "playground" },
    secondaryActions: [
      { label: "Browse Voices", target: "voices" },
      { label: "View Health", target: "health" },
    ],
    statusTiles,
  };
}
