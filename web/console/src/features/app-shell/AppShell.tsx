import { useConnection } from "@features/connection";
import { DeveloperPanel } from "@features/developer/DeveloperPanel";
import { HealthPanel } from "@features/health/HealthPanel";
import { OverviewPanel } from "@features/overview/OverviewPanel";
import { PlaygroundPanel } from "@features/playground/PlaygroundPanel";
import { VoicesPanel } from "@features/voices/VoicesPanel";
import { TokenProvider } from "@shared/auth/TokenContext";
import { AppLayout } from "./AppLayout";
import { ContentArea } from "./ContentArea";
import { NavigationProvider } from "./NavigationContext";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function AppShell() {
  const { token, remember, status, applyToken, logout } = useConnection();

  return (
    <TokenProvider value={token}>
      <NavigationProvider>
        <AppLayout
          sidebar={<Sidebar />}
          topbar={<TopBar status={status} onLogout={logout} />}
        >
          <ContentArea
            panels={{
              overview: (
                <OverviewPanel
                  token={token}
                  remember={remember}
                  status={status}
                  onApplyToken={applyToken}
                  onLogout={logout}
                />
              ),
              voices: <VoicesPanel token={token} />,
              playground: <PlaygroundPanel token={token} />,
              health: <HealthPanel token={token} />,
              developer: <DeveloperPanel />,
            }}
          />
        </AppLayout>
      </NavigationProvider>
    </TokenProvider>
  );
}
