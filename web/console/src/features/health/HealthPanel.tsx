import { useNavigation } from "@features/app-shell/NavigationContext";
import { createMeryApiClient } from "@shared/api/meryApi";
import { QUERY_KEYS } from "@shared/api/queryKeys";
import { Skeleton } from "@shared/ui/Skeleton";
import { StatusDot } from "@shared/ui/StatusDot";
import { useQuery } from "@tanstack/react-query";
import { memo, useMemo } from "react";

interface HealthPanelProps {
  token: string;
}

function HealthPanelBase({ token }: HealthPanelProps) {
  const { navigate } = useNavigation();
  const api = useMemo(() => createMeryApiClient({ token }), [token]);
  const query = useQuery({
    queryKey: QUERY_KEYS.health(token),
    queryFn: () => api.getHealth(),
    enabled: token.length > 0,
    refetchInterval: 30_000,
    staleTime: 20_000,
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
          className="btn btn-secondary"
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
            className="btn btn-secondary"
            onClick={() => navigate("overview")}
          >
            Go to Overview
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => navigate("developer")}
          >
            Open Developer Mode
          </button>
        </div>
      </section>
    );
  }

  const { ready, health_status, total_usable_voices } = query.data;

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
          className="btn btn-ghost"
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
    </section>
  );
}

export const HealthPanel = memo(HealthPanelBase);
