import { useNavigation } from "@features/app-shell/NavigationContext";
import { Button } from "@shared/ui/Button";
import { ConfirmDialog } from "@shared/ui/ConfirmDialog";
import { memo, useState } from "react";

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

function DeveloperPanelBase() {
  const [enabled, setEnabled] = useState(false);
  const { navigate } = useNavigation();

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
          <div className="developer-notice" role="note">
            <strong>Preview only</strong> — this shows the shape of a sanitized
            diagnostic payload. Live diagnostics are not connected in v1.
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
