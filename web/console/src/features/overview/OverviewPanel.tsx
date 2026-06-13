import { useNavigation } from "@features/app-shell/NavigationContext";
import type { ConsoleSection } from "@features/app-shell/routes";
import { ConnectionCard } from "@features/connection";
import type { ConnectionStatus } from "@features/connection/types";
import { createMeryApiClient } from "@shared/api/meryApi";
import { QUERY_KEYS } from "@shared/api/queryKeys";
import { loadVoiceViewModels } from "@shared/api/voiceViewModels";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { deriveOverviewViewModel } from "./overviewViewModel";

interface OverviewPanelProps {
  token: string;
  remember: boolean;
  status: ConnectionStatus;
  onApplyToken: (token: string, remember: boolean) => void;
  onLogout: () => void;
}

export function OverviewPanel({
  token,
  remember,
  status,
  onApplyToken,
  onLogout,
}: OverviewPanelProps) {
  const { navigate } = useNavigation();
  const connected = status === "connected";

  const api = useMemo(
    () => (token ? createMeryApiClient({ token }) : null),
    [token],
  );

  const healthQuery = useQuery({
    queryKey: QUERY_KEYS.health(token),
    queryFn: () => api?.getHealth(),
    enabled: Boolean(token && api),
    staleTime: 20_000,
  });

  const voicesQuery = useQuery({
    queryKey: QUERY_KEYS.voices(token),
    queryFn: () => {
      if (!api) throw new Error("Mery API client is unavailable");
      return loadVoiceViewModels(api);
    },
    enabled: Boolean(token && api && connected),
    staleTime: 30_000,
  });

  const viewModel = deriveOverviewViewModel({
    connectionStatus: status,
    health: healthQuery.data ?? null,
    healthError: healthQuery.isError,
    voices: voicesQuery.data ?? null,
    isHealthLoading: healthQuery.isLoading,
    isVoicesLoading: voicesQuery.isLoading,
  });

  return (
    <section aria-label="Overview">
      <div className="page-header">
        <h2>Overview</h2>
      </div>

      {/* Guided recovery card */}
      <div className="panel overview-recovery">
        <h3 className="overview-headline">{viewModel.headline}</h3>
        <p className="overview-desc">{viewModel.description}</p>

        {viewModel.primaryAction.target === "connect" ? (
          <ConnectionCard
            onSubmit={onApplyToken}
            onLogout={onLogout}
            currentToken={token}
            currentRemember={remember}
          />
        ) : (
          <button
            type="button"
            className="button button-primary"
            onClick={() =>
              navigate(viewModel.primaryAction.target as ConsoleSection)
            }
          >
            {viewModel.primaryAction.label}
          </button>
        )}

        {viewModel.secondaryActions.length > 0 && (
          <div className="overview-secondary-actions">
            {viewModel.secondaryActions.map((action) => (
              <a
                key={action.target}
                href={`#${action.target}`}
                onClick={(e) => {
                  e.preventDefault();
                  navigate(action.target as ConsoleSection);
                }}
              >
                {action.label}
              </a>
            ))}
          </div>
        )}
      </div>

      {/* Status tiles */}
      <output
        className="overview-tiles"
        aria-label="System status"
        aria-live="polite"
      >
        {viewModel.statusTiles.map((tile) => (
          <div
            key={tile.label}
            className={`overview-tile overview-tile--${tile.level}`}
          >
            <span className="overview-tile-label">{tile.label}</span>
            <span className="overview-tile-value">{tile.value}</span>
          </div>
        ))}
      </output>
    </section>
  );
}
