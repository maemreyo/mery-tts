import { DeveloperPanel } from "@features/developer/DeveloperPanel";
import { HealthPanel } from "@features/health/HealthPanel";
import { PlaygroundPanel } from "@features/playground/PlaygroundPanel";
import { VoicesPanel } from "@features/voices/VoicesPanel";
import {
  clearSession,
  persistSession,
  readInitialSession,
} from "@shared/auth/session";
import { t } from "@shared/i18n/messages";
import { Panel } from "@shared/ui/Panel";
import { useEffect, useState } from "react";

export function AppShell() {
  const [session, setSession] = useState(readInitialSession);

  useEffect(() => {
    persistSession(session);
  }, [session]);

  return (
    <main className="console-shell">
      <Panel>
        <h1>{t("appTitle")}</h1>
        <p>{t("appDescription")}</p>
        <nav aria-label="User Mode navigation">
          <a href="#voices">Voices</a> <a href="#playground">Playground</a>{" "}
          <a href="#health">Health</a>
        </nav>
        <div className="field-row">
          <label>
            {t("bearerToken")}
            <input
              aria-label={t("bearerToken")}
              type="password"
              value={session.token}
              onChange={(event) =>
                setSession((current) => ({
                  ...current,
                  token: event.currentTarget.value,
                }))
              }
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={session.remember}
              onChange={(event) =>
                setSession((current) => ({
                  ...current,
                  remember: event.currentTarget.checked,
                }))
              }
            />
            {t("rememberDevice")}
          </label>
          <button type="button" onClick={() => setSession(clearSession())}>
            {t("logout")}
          </button>
        </div>
      </Panel>
      <Panel>
        <div id="voices">
          <VoicesPanel token={session.token} />
        </div>
      </Panel>
      <Panel>
        <div id="playground">
          <PlaygroundPanel token={session.token} />
        </div>
      </Panel>
      <Panel>
        <div id="health">
          <HealthPanel token={session.token} />
        </div>
      </Panel>
      <Panel>
        <DeveloperPanel />
      </Panel>
    </main>
  );
}
