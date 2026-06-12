import { createMeryApiClient } from "@shared/api/meryApi";
import { Skeleton } from "@shared/ui/Skeleton";
import { StatusDot } from "@shared/ui/StatusDot";
import { useQuery } from "@tanstack/react-query";
import { memo, useMemo } from "react";

interface HealthPanelProps {
  token: string;
}

function HealthPanelBase({ token }: HealthPanelProps) {
  const api = useMemo(() => createMeryApiClient({ token }), [token]);
  const query = useQuery({
    queryKey: ["health", token],
    queryFn: () => api.getHealth(),
    enabled: token.length > 0,
    refetchInterval: 30_000,
    staleTime: 20_000,
  });

  if (!token) {
    return (
      <section aria-label="Health">
        <div className="page-header">
          <h2>Health</h2>
          <p>Enter a bearer token to inspect server health.</p>
        </div>
      </section>
    );
  }

  if (query.isLoading) {
    return (
      <section aria-label="Health">
        <div className="page-header">
          <h2>Health</h2>
        </div>
        <div className="health-grid">
          {Array.from({ length: 3 }, (_, i) => (
            <div key={i} className="health-stat">
              <Skeleton variant="line-sm" width="60%" />
              <Skeleton variant="line-lg" width="40%" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (query.isError || !query.data) {
    return (
      <section aria-label="Health">
        <div className="page-header">
          <h2>Health</h2>
          <p>Could not reach the server. Check the bearer token and local server status.</p>
        </div>
      </section>
    );
  }

  const { ready, health_status, total_usable_voices } = query.data;

  return (
    <section aria-label="Health">
      <div className="page-header">
        <h2>Health</h2>
        <p>Live status of the local Mery server.</p>
      </div>

      <div className="health-grid">
        <div className="health-stat">
          <div className="health-stat-label">Readiness</div>
          <div className={`health-stat-value ${ready ? "health-stat-value--ready" : ""}`}>
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
      </div>
    </section>
  );
}

export const HealthPanel = memo(HealthPanelBase);
