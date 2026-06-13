import type { StorageCleanupTarget } from "@api/generated/client";
import { useNavigation } from "@features/app-shell/NavigationContext";
import { createMeryApiClient } from "@shared/api/meryApi";
import { QUERY_KEYS } from "@shared/api/queryKeys";
import { Skeleton } from "@shared/ui/Skeleton";
import { StatusDot } from "@shared/ui/StatusDot";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { memo, useMemo } from "react";

interface HealthPanelProps {
  token: string;
}

function formatBytes(bytes: number): string {
  if (bytes >= 1_073_741_824) {
    return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
  }
  return `${(bytes / 1_048_576).toFixed(1)} MB`;
}

const ENGINE_STATUS_BADGE: Record<
  "available" | "degraded" | "unavailable",
  string
> = {
  available: "badge badge--success",
  degraded: "badge badge--warning",
  unavailable: "badge badge--error",
};

function HealthPanelBase({ token }: HealthPanelProps) {
  const { navigate } = useNavigation();
  const queryClient = useQueryClient();
  const api = useMemo(() => createMeryApiClient({ token }), [token]);

  const query = useQuery({
    queryKey: QUERY_KEYS.health(token),
    queryFn: () => api.getHealthV2(),
    enabled: token.length > 0,
    refetchInterval: 30_000,
    staleTime: 20_000,
  });

  const connected = query.isSuccess;

  const storageQuery = useQuery({
    queryKey: QUERY_KEYS.storage(token),
    queryFn: () => api.getStorage(),
    enabled: Boolean(token && connected),
    staleTime: 60_000,
  });

  const cleanupMutation = useMutation({
    mutationFn: (target: StorageCleanupTarget) => api.cleanupStorage(target),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.storage(token),
      });
    },
  });

  // State a: no token
  if (!token) {
    return (
      <section aria-label="Health">
        <div className="page-header">
          <h2>Health</h2>
          <p>Enter a bearer token above.</p>
        </div>
        <button
          type="button"
          className="button button-secondary"
          onClick={() => navigate("overview")}
        >
          Go to Overview
        </button>
      </section>
    );
  }

  // State b: loading
  if (query.isLoading) {
    return (
      <section aria-label="Health">
        <div className="page-header">
          <h2>Health</h2>
        </div>
        <div className="health-grid">
          {(["readiness", "status", "voices"] as const).map((slot) => (
            <div key={slot} className="health-stat">
              <Skeleton variant="line-sm" width="60%" />
              <Skeleton variant="line-lg" width="40%" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  // State c: error / unreachable
  if (query.isError || !query.data) {
    return (
      <section aria-label="Health">
        <div className="page-header">
          <h2>Health</h2>
          <p>Cannot reach the Mery server. Is mery serve running?</p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            type="button"
            className="button button-secondary"
            onClick={() => navigate("overview")}
          >
            Go to Overview
          </button>
          <button
            type="button"
            className="button"
            onClick={() => navigate("developer")}
          >
            Open Developer Mode
          </button>
        </div>
      </section>
    );
  }

  const { ready, health_status, total_usable_voices, engines } = query.data;

  // State d: connected but not ready
  if (!ready) {
    return (
      <section aria-label="Health">
        <div className="page-header">
          <h2>Health</h2>
          <p>Server is running but not ready.</p>
          <p style={{ fontSize: 13 }}>{health_status}</p>
        </div>
        <button
          type="button"
          className="button"
          onClick={() => navigate("developer")}
        >
          Open Developer Mode for diagnostics
        </button>
      </section>
    );
  }

  // State e: connected + ready
  return (
    <section aria-label="Health">
      <div className="page-header">
        <h2>Health</h2>
        <p>Live status of the local Mery server.</p>
      </div>

      <output className="health-grid" aria-label="Health status">
        <div className="health-stat">
          <div className="health-stat-label">Readiness</div>
          <div
            className={`health-stat-value ${ready ? "health-stat-value--ready" : ""}`}
          >
            <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <StatusDot level={ready ? "ready" : "blocked"} pulse={ready} />
              {ready ? "Ready" : "Not ready"}
            </span>
          </div>
        </div>

        <div className="health-stat">
          <div className="health-stat-label">Status</div>
          <div className="health-stat-value" style={{ fontSize: 16 }}>
            {health_status}
          </div>
        </div>

        <div className="health-stat">
          <div className="health-stat-label">Usable voices</div>
          <div className="health-stat-value">{total_usable_voices}</div>
        </div>
      </output>

      <p
        style={{
          fontSize: 12,
          color: "var(--color-muted, #888)",
          marginTop: 8,
        }}
      >
        Live status — refreshes every 30 s.
      </p>

      {/* Engine health section */}
      {engines && engines.length > 0 && (
        <div style={{ marginTop: "var(--sp-6)" }}>
          <h3
            style={{
              fontSize: 13,
              fontWeight: 700,
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              marginBottom: "var(--sp-3)",
              marginTop: 0,
            }}
          >
            Engine Status
          </h3>
          <div className="engine-grid">
            {engines.map((engine) => (
              <div
                key={engine.engine_id}
                className={`engine-card engine-card--${engine.status}`}
              >
                <div className="engine-card-id">{engine.engine_id}</div>
                <div style={{ marginBottom: 4 }}>
                  <span className={ENGINE_STATUS_BADGE[engine.status]}>
                    {engine.status}
                  </span>
                </div>
                <div className="engine-card-stat">
                  {engine.usable_voice_count}{" "}
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 500,
                      color: "var(--text-muted)",
                    }}
                  >
                    usable voices
                  </span>
                </div>
                {engine.reason && (
                  <div className="engine-card-reason">{engine.reason}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Storage section */}
      <div className="storage-section">
        <h3>Storage</h3>

        {storageQuery.isLoading && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <Skeleton variant="line-sm" width="80%" />
            <Skeleton variant="line-sm" width="60%" />
            <Skeleton variant="line-sm" width="70%" />
          </div>
        )}

        {storageQuery.data && (
          <>
            {storageQuery.data.advisory?.status === "warn" && (
              <div className="storage-advisory" role="alert">
                {storageQuery.data.advisory.message}
              </div>
            )}

            <div className="storage-breakdown">
              <div className="storage-row">
                <span className="storage-row-label">Total used</span>
                <span className="storage-row-value">
                  {formatBytes(storageQuery.data.used_bytes)}
                </span>
              </div>
              {storageQuery.data.free_bytes != null && (
                <div className="storage-row">
                  <span className="storage-row-label">Free</span>
                  <span className="storage-row-value">
                    {formatBytes(storageQuery.data.free_bytes)}
                  </span>
                </div>
              )}
              {(["models", "cache", "logs", "diagnostics"] as const).map(
                (key) => (
                  <div key={key} className="storage-row">
                    <span className="storage-row-label">{key}</span>
                    <span className="storage-row-value">
                      {formatBytes(storageQuery.data.breakdown[key])}
                    </span>
                  </div>
                ),
              )}
            </div>

            <div className="storage-actions">
              {(["cache", "logs", "diagnostics"] as const).map((target) => (
                <button
                  key={target}
                  type="button"
                  className="button button-secondary"
                  disabled={cleanupMutation.isPending}
                  onClick={() => cleanupMutation.mutate(target)}
                >
                  Clean {target}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export const HealthPanel = memo(HealthPanelBase);
