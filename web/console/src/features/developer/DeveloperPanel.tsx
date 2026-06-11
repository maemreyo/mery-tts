import { useState } from "react";

export function DeveloperPanel() {
  const [enabled, setEnabled] = useState(false);

  return (
    <section aria-label="Developer Mode">
      <h2>Developer Mode</h2>
      <button
        type="button"
        aria-pressed={enabled}
        onClick={() => setEnabled((value) => !value)}
      >
        {enabled ? "Hide Developer Mode" : "Show Developer Mode"}
      </button>
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
          <pre>
            {JSON.stringify(
              { route: "/v1/health", mode: "pull", sanitized: true },
              null,
              2,
            )}
          </pre>
        </div>
      ) : null}
    </section>
  );
}
