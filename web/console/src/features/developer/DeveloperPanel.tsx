import { useNavigation } from "@features/app-shell/NavigationContext";
import { createMeryApiClient } from "@shared/api/meryApi";
import { QUERY_KEYS } from "@shared/api/queryKeys";
import { useToken } from "@shared/auth/TokenContext";
import { Button } from "@shared/ui/Button";
import { ConfirmDialog } from "@shared/ui/ConfirmDialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { memo, useMemo, useState } from "react";

const sanitizedExample = {
  route: "/v1/health",
  mode: "pull",
  sanitized: true,
  redacted: [
    "raw_private_text",
    "bearer_token",
    "reference_audio",
    "private_path",
  ],
};

function severityClass(severity: string): string {
  if (severity === "warning") return "badge--warning";
  if (severity === "error") return "badge--error";
  return "badge--neutral";
}

function checkValClass(value: string): string {
  if (value === "ok") return "diagnostics-check-val--ok";
  if (value === "warn") return "diagnostics-check-val--warn";
  if (value === "error" || value === "fail")
    return "diagnostics-check-val--error";
  return "diagnostics-check-val--other";
}

function DeveloperPanelBase() {
  const [enabled, setEnabled] = useState(false);
  const { navigate } = useNavigation();
  const token = useToken();
  const queryClient = useQueryClient();

  const api = useMemo(
    () => (token ? createMeryApiClient({ token }) : null),
    [token],
  );

  const diagnosticsQuery = useQuery({
    queryKey: QUERY_KEYS.diagnostics(token),
    queryFn: () => api?.getDiagnostics(),
    enabled: !!token && !!api,
  });

  const runDoctorMutation = useMutation({
    mutationFn: () => {
      if (!api) throw new Error("No API client");
      return api.runDiagnostics();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.diagnostics(token),
      });
    },
  });

  const checks = diagnosticsQuery.data?.checks ?? {};
  const events = [...(diagnosticsQuery.data?.events ?? [])]
    .sort(
      (a, b) =>
        new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime(),
    )
    .slice(0, 10);

  return (
    <section aria-label="Developer">
      <div className="page-header">
        <h2>Developer</h2>
        <p>Advanced diagnostics for Mery.</p>
      </div>
      <Button
        type="button"
        aria-pressed={enabled}
        aria-label={enabled ? "Hide developer tools" : "Developer tools"}
        onClick={() => setEnabled((value) => !value)}
      >
        {enabled ? "Hide developer tools" : "Developer tools"}
      </Button>
      {enabled ? (
        <div className="developer-panel">
          {!token ? (
            <p>Connect to run diagnostics.</p>
          ) : (
            <>
              {/* Part A — Diagnostics checks */}
              {Object.keys(checks).length > 0 && (
                <div className="diagnostics-checks">
                  {Object.entries(checks).map(([key, value]) => (
                    <div key={key} className="diagnostics-check-row">
                      <span className="diagnostics-check-key">{key}</span>
                      <span className={checkValClass(value)}>{value}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Part B — Recent diagnostic events */}
              {events.length > 0 && (
                <div className="diagnostics-events">
                  {events.map((event) => (
                    <div key={event.event_id} className="diagnostics-event">
                      <span
                        className={`badge ${severityClass(event.severity)}`}
                      >
                        {event.severity}
                      </span>
                      <span className="diagnostics-event-source">
                        {event.source}
                      </span>
                      <span className="diagnostics-event-message">
                        — {event.message}
                      </span>
                      <span className="diagnostics-event-source">
                        {event.occurred_at}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Part C — Doctor actions */}
              <Button
                type="button"
                disabled={runDoctorMutation.isPending}
                onClick={() => runDoctorMutation.mutate()}
              >
                {runDoctorMutation.isPending ? "Running…" : "Run doctor check"}
              </Button>
            </>
          )}

          {/* Preview notice — collapsed by default */}
          <details style={{ marginTop: "var(--sp-3)" }}>
            <summary
              style={{
                fontSize: 12,
                color: "var(--text-muted)",
                cursor: "pointer",
              }}
            >
              Show sanitized payload example
            </summary>
            <div className="developer-notice" role="note">
              <strong>Preview only</strong> — this shows the shape of a
              sanitized diagnostic payload. Live diagnostics are not connected
              in v1.
            </div>
            <ConfirmDialog
              title="Sanitized Developer Mode payload"
              description="Inspect a schema-shaped example without secrets or private user data."
              onConfirm={() => undefined}
            >
              <Button type="button">Inspect schema example</Button>
            </ConfirmDialog>
            <pre aria-label="Sanitized diagnostic payload example">
              {JSON.stringify(sanitizedExample, null, 2)}
            </pre>
          </details>

          <button
            type="button"
            className="button"
            onClick={() => navigate("overview")}
          >
            ← Overview
          </button>
        </div>
      ) : null}
    </section>
  );
}

export const DeveloperPanel = memo(DeveloperPanelBase);
