import type { ConnectionStatus } from "@features/connection/types";
import { Button } from "@shared/ui/Button";
import { useNavigation } from "./NavigationContext";

interface TopBarProps {
  status: ConnectionStatus;
  onLogout: () => void;
}

const sectionTitles: Record<string, string> = {
  overview: "Overview",
  voices: "Voices",
  playground: "Playground",
  health: "Health",
  developer: "Developer",
};

export function TopBar({ status, onLogout }: TopBarProps) {
  const { activeSection, navigate } = useNavigation();

  const statusLabel =
    status === "connected"
      ? "Connected"
      : status === "checking"
        ? "Checking…"
        : "Disconnected";

  return (
    <header className="topbar">
      <span className="topbar-title">
        {sectionTitles[activeSection] ?? "Console"}
      </span>
      <div className="topbar-connection">
        <span
          className={`topbar-status topbar-status--${status}`}
          aria-label={`Connection: ${statusLabel}`}
        >
          <span className="topbar-status-dot" aria-hidden="true" />
          {statusLabel}
        </span>
        {status === "disconnected" && (
          <button
            type="button"
            className="topbar-connect-link"
            onClick={() => navigate("overview")}
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
