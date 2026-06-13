import { useConnection } from "@features/connection";
import { DeveloperPanel } from "@features/developer/DeveloperPanel";
import { HealthPanel } from "@features/health/HealthPanel";
import { OverviewPanel } from "@features/overview/OverviewPanel";
import { PlaygroundPanel } from "@features/playground/PlaygroundPanel";
import { SessionActivityProvider } from "@features/session/SessionActivity";
import { VoicesPanel } from "@features/voices/VoicesPanel";
import { TokenProvider } from "@shared/auth/TokenContext";
import { useState } from "react";
import { AppLayout } from "./AppLayout";
import { ContentArea } from "./ContentArea";
import { NavigationProvider } from "./NavigationContext";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function AppShell() {
  const { token, remember, status, applyToken, logout } = useConnection();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <SessionActivityProvider>
      <TokenProvider value={token}>
        <NavigationProvider>
          <AppLayout
            sidebar={
              <Sidebar
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
              />
            }
            topbar={
              <TopBar
                status={status}
                onLogout={logout}
                onMenuOpen={() => setSidebarOpen(true)}
              />
            }
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
    </SessionActivityProvider>
  );
}
