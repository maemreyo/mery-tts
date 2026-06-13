import { useNavigation } from "@features/app-shell/NavigationContext";
import type { ConsoleSection } from "@features/app-shell/routes";
import { ConnectionCard } from "@features/connection";
import type { ConnectionStatus } from "@features/connection/types";
import { useSessionActivity } from "@features/session/SessionActivity";
import { createMeryApiClient } from "@shared/api/meryApi";
import { QUERY_KEYS } from "@shared/api/queryKeys";
import { loadVoiceViewModels } from "@shared/api/voiceViewModels";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { deriveOverviewViewModel } from "./overviewViewModel";

function formatRelativeTime(isoStr: string): string {
  const elapsed = (Date.now() - new Date(isoStr).getTime()) / 1000;
  if (elapsed < 60) return "just now";
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)}m ago`;
  return `${Math.floor(elapsed / 3600)}h ago`;
}

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
  const { lastSmoke, lastInstall } = useSessionActivity();
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
    hasToken: Boolean(token),
    health: healthQuery.data ?? null,
    healthError: healthQuery.isError,
    voices: voicesQuery.data ?? null,
    isHealthLoading: healthQuery.isLoading,
    isVoicesLoading: voicesQuery.isLoading,
    engines: ((
      healthQuery.data as
        | { engines?: { engine_id: string; status: string }[] }
        | undefined
    )?.engines ?? []) as ReadonlyArray<{ engine_id: string; status: string }>,
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

      {(lastSmoke || lastInstall) && (
        <div className="overview-last-actions" aria-label="Recent activity">
          <span className="overview-last-actions-label">Recent</span>
          {lastSmoke && (
            <div
              className={`overview-last-action overview-last-action--${lastSmoke.ok ? "ok" : "error"}`}
            >
              <span className="last-action-icon">
                {lastSmoke.ok ? "✓" : "✗"}
              </span>
              <span className="last-action-text">
                Smoke — {lastSmoke.voiceLabel}
              </span>
              <span className="last-action-time">
                {formatRelativeTime(lastSmoke.timestamp)}
              </span>
            </div>
          )}
          {lastInstall && (
            <div
              className={`overview-last-action overview-last-action--${lastInstall.status === "succeeded" ? "ok" : "error"}`}
            >
              <span className="last-action-icon">
                {lastInstall.status === "succeeded" ? "✓" : "✗"}
              </span>
              <span className="last-action-text">
                Install — {lastInstall.voiceLabel}
              </span>
              <span className="last-action-time">
                {formatRelativeTime(lastInstall.timestamp)}
              </span>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
