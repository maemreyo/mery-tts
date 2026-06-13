import { createMeryApiClient } from "@shared/api/meryApi";
import { useToken } from "@shared/auth/TokenContext";
import { StatusDot } from "@shared/ui/StatusDot";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useNavigation } from "./NavigationContext";
import { type ConsoleSection, consoleSections } from "./routes";

/* ── Section icons ────────────────────────────────────────────────────── */

function OverviewIcon() {
  return (
    <svg
      aria-hidden="true"
      className="nav-item-icon"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="1" y="1" width="6" height="6" rx="1" />
      <rect x="9" y="1" width="6" height="6" rx="1" />
      <rect x="1" y="9" width="6" height="6" rx="1" />
      <rect x="9" y="9" width="6" height="6" rx="1" />
    </svg>
  );
}

function VoicesIcon() {
  return (
    <svg
      aria-hidden="true"
      className="nav-item-icon"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M10 3.5c1.5 1 2.5 2.6 2.5 4.5s-1 3.5-2.5 4.5" />
      <path d="M12 1c2.5 1.5 4 4 4 7s-1.5 5.5-4 7" />
      <rect x="1" y="5" width="5" height="6" rx="1" />
      <path d="M6 6.5l4-3v9l-4-3" />
    </svg>
  );
}

function PlaygroundIcon() {
  return (
    <svg
      aria-hidden="true"
      className="nav-item-icon"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polygon points="4,2 14,8 4,14" />
    </svg>
  );
}

function HealthIcon() {
  return (
    <svg
      aria-hidden="true"
      className="nav-item-icon"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="1,8 4,8 6,3 8,13 10,6 12,8 15,8" />
    </svg>
  );
}

function DeveloperIcon() {
  return (
    <svg
      aria-hidden="true"
      className="nav-item-icon"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="5,4 1,8 5,12" />
      <polyline points="11,4 15,8 11,12" />
      <line x1="9" y1="2" x2="7" y2="14" />
    </svg>
  );
}

const sectionIcons: Record<ConsoleSection, React.ReactNode> = {
  overview: <OverviewIcon />,
  voices: <VoicesIcon />,
  playground: <PlaygroundIcon />,
  health: <HealthIcon />,
  developer: <DeveloperIcon />,
};

/* ── Server status ────────────────────────────────────────────────────── */

type StatusLevel = "ready" | "degraded" | "blocked" | "unknown";

function useServerStatus(): { level: StatusLevel; label: string } {
  const token = useToken();
  const api = useMemo(
    () => (token ? createMeryApiClient({ token }) : null),
    [token],
  );

  const query = useQuery({
    queryKey: ["health", token],
    queryFn: () => api?.getHealth(),
    enabled: Boolean(token && api),
    refetchInterval: 30_000,
    staleTime: 20_000,
  });

  if (!token) return { level: "unknown", label: "No token — enter one above" };
  if (query.isLoading) return { level: "unknown", label: "Checking server…" };
  if (query.isError) return { level: "blocked", label: "Server unreachable" };
  if (!query.data) return { level: "unknown", label: "No data" };
  if (query.data.ready) return { level: "ready", label: "Server ready" };
  return { level: "degraded", label: "Server degraded" };
}

/* ── Sidebar ──────────────────────────────────────────────────────────── */

export function Sidebar() {
  const { activeSection, navigate } = useNavigation();
  const { level, label } = useServerStatus();

  return (
    <nav className="sidebar" aria-label="Main navigation">
      {/* Brand */}
      <button
        type="button"
        className="sidebar-brand"
        onClick={() => navigate("overview")}
      >
        <span className="sidebar-brand-icon" aria-hidden="true">
          <svg
            aria-hidden="true"
            width="14"
            height="14"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M10 3.5c1.5 1 2.5 2.6 2.5 4.5s-1 3.5-2.5 4.5" />
            <rect x="1" y="5" width="5" height="6" rx="1" />
            <path d="M6 6.5l4-3v9l-4-3" />
          </svg>
        </span>
        <div>
          <div className="sidebar-brand-name">Mery</div>
          <div className="sidebar-brand-tag">Console</div>
        </div>
      </button>

      {/* Navigation */}
      <div className="sidebar-nav" aria-label="Console sections">
        <span className="sidebar-nav-label">User Mode</span>

        {consoleSections
          .filter((s) => s.id !== "developer")
          .map((section) => (
            <a
              key={section.id}
              href={section.hash}
              className="nav-item"
              aria-current={activeSection === section.id ? "page" : undefined}
              onClick={(e) => {
                e.preventDefault();
                navigate(section.id);
              }}
            >
              {sectionIcons[section.id]}
              {section.label}
            </a>
          ))}

        <span className="sidebar-nav-label">Advanced</span>

        <button
          type="button"
          className="nav-item"
          aria-current={activeSection === "developer" ? "page" : undefined}
          onClick={() => navigate("developer")}
        >
          {sectionIcons.developer}
          Developer
        </button>
      </div>

      {/* Footer: server status */}
      <div className="sidebar-footer">
        <div className="server-status">
          <StatusDot level={level} pulse={level === "ready"} label={label} />
          <span>{label}</span>
        </div>
      </div>
    </nav>
  );
}
