import { DeveloperPanel } from "@features/developer/DeveloperPanel";
import { HealthPanel } from "@features/health/HealthPanel";
import { PlaygroundPanel } from "@features/playground/PlaygroundPanel";
import { VoicesPanel } from "@features/voices/VoicesPanel";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  clearSession,
  persistSession,
  readInitialSession,
} from "@shared/auth/session";
import { TokenProvider } from "@shared/auth/TokenContext";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AppLayout } from "./AppLayout";
import { ContentArea } from "./ContentArea";
import { NavigationProvider } from "./NavigationContext";
import { Sidebar } from "./Sidebar";
import { TopBar, type SessionFormValues } from "./TopBar";

const sessionSchema = z.object({
  token: z.string().trim().max(4096, "Bearer token is too long."),
  remember: z.boolean(),
});

export function AppShell() {
  const [session, setSession] = useState(readInitialSession);

  const form = useForm<SessionFormValues>({
    resolver: zodResolver(sessionSchema),
    values: session,
  });

  useEffect(() => {
    persistSession(session);
  }, [session]);

  const applySession = form.handleSubmit((values) => setSession(values));

  const logout = () => {
    const cleared = clearSession();
    setSession(cleared);
    form.reset(cleared);
  };

  return (
    <TokenProvider value={session.token}>
      <NavigationProvider>
        <AppLayout
          sidebar={<Sidebar />}
          topbar={
            <TopBar form={form} onSubmit={applySession} onLogout={logout} />
          }
        >
          <ContentArea
            panels={{
              voices:     <VoicesPanel token={session.token} />,
              playground: <PlaygroundPanel token={session.token} />,
              health:     <HealthPanel token={session.token} />,
              developer:  <DeveloperPanel />,
            }}
          />
        </AppLayout>
      </NavigationProvider>
    </TokenProvider>
  );
}
