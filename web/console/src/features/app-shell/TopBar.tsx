import type { ConnectionStatus } from "@features/connection/types";
import { Button } from "@shared/ui/Button";
import { useNavigation } from "./NavigationContext";

interface TopBarProps {
  status: ConnectionStatus;
  onLogout: () => void;
  onMenuOpen: () => void;
}

const sectionTitles: Record<string, string> = {
  overview: "Overview",
  voices: "Voices",
  playground: "Playground",
  health: "Health",
  developer: "Developer",
};

export function TopBar({ status, onLogout, onMenuOpen }: TopBarProps) {
  const { activeSection, navigate } = useNavigation();

  const statusLabel =
    status === "connected"
      ? "Connected"
      : status === "checking"
        ? "Checking…"
        : "Disconnected";

  return (
    <header className="topbar">
      <button
        type="button"
        className="topbar-hamburger"
        aria-label="Open navigation"
        onClick={onMenuOpen}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="currentColor"
          aria-hidden="true"
        >
          <rect x="2" y="4" width="14" height="1.5" rx="0.75" />
          <rect x="2" y="8.25" width="14" height="1.5" rx="0.75" />
          <rect x="2" y="12.5" width="14" height="1.5" rx="0.75" />
        </svg>
      </button>
      <span className="topbar-title">
        {sectionTitles[activeSection] ?? "Console"}
      </span>
      <div className="topbar-connection">
        <span
          className={`topbar-status topbar-status--${status}`}
          aria-label={`Connection: ${statusLabel}`}
        >
          <span className="topbar-status-dot" aria-hidden="true" />
          <span className="topbar-status-label">{statusLabel}</span>
        </span>
        {status === "disconnected" && (
          <button
            type="button"
            className="topbar-connect-link"
            onClick={() => navigate("overview")}
            aria-label="Connect to Mery"
          >
            Connect →
          </button>
        )}
      </div>
      <Button type="button" onClick={onLogout}>
        Log out
      </Button>
    </header>
  );
}
