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

  return (
    <section aria-label="Developer Mode">
      <h2>Developer Mode</h2>
      <Button
        type="button"
        aria-pressed={enabled}
        onClick={() => setEnabled((value) => !value)}
      >
        {enabled ? "Hide Developer Mode" : "Show Developer Mode"}
      </Button>
      {enabled ? (
        <div className="developer-panel">
          <p>
            Pull-based diagnostics only. Live event streams remain a later
            enhancement.
          </p>
          <p>
            Raw private text, bearer tokens, reference audio, and private
            filesystem paths must stay redacted.
          </p>
          <ConfirmDialog
            title="Sanitized Developer Mode payload"
            description="Inspect a schema-shaped example without secrets or private user data."
            onConfirm={() => undefined}
          >
            <Button type="button">Inspect schema example</Button>
          </ConfirmDialog>
          <pre>{JSON.stringify(sanitizedExample, null, 2)}</pre>
        </div>
      ) : null}
    </section>
  );
}

export const DeveloperPanel = memo(DeveloperPanelBase);
