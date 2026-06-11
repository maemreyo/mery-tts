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
import { Button } from "@shared/ui/Button";
import { FieldGroup, FormField } from "@shared/ui/FormField";
import { Panel } from "@shared/ui/Panel";
import { SwitchField } from "@shared/ui/SwitchField";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { SectionTabs } from "./SectionTabs";

const sessionSchema = z.object({
  token: z.string().trim().max(4096, "Bearer token is too long."),
  remember: z.boolean(),
});

type SessionFormValues = z.infer<typeof sessionSchema>;

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
    <main className="console-shell">
      <Panel>
        <h1>Mery Console</h1>
        <p>
          Local-first TTS control plane. User Mode is recovery-focused;
          Developer Mode remains opt-in.
        </p>
        <form className="session-form" onSubmit={applySession}>
          <FieldGroup>
            <FormField
              label="Bearer token"
              type="password"
              autoComplete="off"
              error={form.formState.errors.token?.message}
              {...form.register("token")}
            />
            <SwitchField
              checked={form.watch("remember")}
              label="Remember on this device"
              onCheckedChange={(checked) => form.setValue("remember", checked)}
            />
            <Button type="submit" variant="primary">
              Use token
            </Button>
            <Button type="button" onClick={logout}>
              Log out
            </Button>
          </FieldGroup>
        </form>
      </Panel>
      <SectionTabs
        panels={{
          voices: (
            <Panel>
              <div id="voices">
                <VoicesPanel token={session.token} />
              </div>
            </Panel>
          ),
          playground: (
            <Panel>
              <div id="playground">
                <PlaygroundPanel token={session.token} />
              </div>
            </Panel>
          ),
          health: (
            <Panel>
              <div id="health">
                <HealthPanel token={session.token} />
              </div>
            </Panel>
          ),
          developer: (
            <Panel>
              <div id="developer">
                <DeveloperPanel />
              </div>
            </Panel>
          ),
        }}
      />
    </main>
  );
}
