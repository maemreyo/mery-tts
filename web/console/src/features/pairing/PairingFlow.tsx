import type { PairingChallengeResponse } from "@api/generated/client";
import { createMeryApiClient } from "@shared/api/meryApi";
import { useMutation } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";

interface PairingFlowProps {
  token: string;
}

function useCountdown(expiresAt: string | null): number {
  const [remaining, setRemaining] = useState(0);

  useEffect(() => {
    if (!expiresAt) return;
    const tick = () => {
      const secs = Math.max(
        0,
        Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000),
      );
      setRemaining(secs);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAt]);

  return remaining;
}

function fmt(secs: number): string {
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return m + ":" + String(s).padStart(2, "0");
}

/**
 * Attempt to auto-fill the pairing code into a zreader overlay on the page.
 * zreader injects a form with data-zr-mery-pairing-code="" on its input.
 * Returns true if the auto-fill + submit succeeded.
 */
function tryAutoFillZreader(code: string): boolean {
  try {
    const input = document.querySelector<HTMLInputElement>(
      "[data-zr-mery-pairing-code]",
    );
    if (!input) return false;

    const nativeSetter = Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )?.set;
    nativeSetter?.call(input, code);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));

    const form = input.closest<HTMLFormElement>("[data-zr-mery-pair-form]");
    if (form) {
      form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

export function PairingFlow({ token }: PairingFlowProps) {
  const api = useMemo(() => createMeryApiClient({ token }), [token]);
  const [challenge, setChallenge] = useState<PairingChallengeResponse | null>(
    null,
  );
  const [copied, setCopied] = useState(false);
  const [autoFilled, setAutoFilled] = useState(false);
  const [autoFillFailed, setAutoFillFailed] = useState(false);
  const copyTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const generateMutation = useMutation({
    mutationFn: () => api.createPairingChallenge(),
    onSuccess: (data) => {
      setChallenge(data);
      setAutoFilled(false);
      setAutoFillFailed(false);
    },
  });

  const remaining = useCountdown(challenge?.expires_at ?? null);
  const expired = remaining === 0 && challenge !== null;

  function copyCode() {
    if (!challenge) return;
    navigator.clipboard.writeText(challenge.pairing_code).then(() => {
      setCopied(true);
      if (copyTimeout.current) clearTimeout(copyTimeout.current);
      copyTimeout.current = setTimeout(() => setCopied(false), 2500);
    });
  }

  function connectZreader() {
    if (!challenge) return;
    const ok = tryAutoFillZreader(challenge.pairing_code);
    if (ok) {
      setAutoFilled(true);
    } else {
      setAutoFillFailed(true);
      copyCode();
    }
  }

  if (!challenge) {
    return (
      <div className="pairing-flow">
        <div className="pairing-flow-header">
          <span className="pairing-flow-title">Pair a client</span>
          <span className="pairing-flow-subtitle">
            Connect Zam Reader or any compatible client
          </span>
        </div>
        <button
          type="button"
          className="button button-secondary"
          disabled={generateMutation.isPending}
          onClick={() => generateMutation.mutate()}
        >
          {generateMutation.isPending ? "Generating…" : "Generate pairing code"}
        </button>
        {generateMutation.isError && (
          <p className="pairing-error">Failed to generate code — check connection.</p>
        )}
      </div>
    );
  }

  return (
    <div className="pairing-flow pairing-flow--active">
      <div className="pairing-flow-header">
        <span className="pairing-flow-title">Pair a client</span>
        {expired ? (
          <span className="pairing-badge pairing-badge--expired">Expired</span>
        ) : (
          <span className="pairing-badge pairing-badge--live">
            {fmt(remaining)}
          </span>
        )}
      </div>

      {expired ? (
        <div className="pairing-expired">
          <p>Code expired. Generate a new one.</p>
          <button
            type="button"
            className="button button-secondary"
            onClick={() => { setChallenge(null); generateMutation.reset(); }}
          >
            New code
          </button>
        </div>
      ) : (
        <>
          {/* Big code display */}
          <div className="pairing-code-row">
            <span className="pairing-code" aria-label={"Pairing code: " + challenge.pairing_code.split("").join(" ")}>
              {challenge.pairing_code.split("").map((ch, i) => (
                <span key={i} className="pairing-code-char">{ch}</span>
              ))}
            </span>
            <button
              type="button"
              className={"pairing-copy-btn" + (copied ? " pairing-copy-btn--done" : "")}
              onClick={copyCode}
              aria-label="Copy pairing code"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>

          {/* One-click zreader connect */}
          {autoFilled ? (
            <p className="pairing-autofill-ok">
              ✓ Code sent to Zam Reader — check the extension overlay.
            </p>
          ) : (
            <button
              type="button"
              className="button button-primary pairing-connect-btn"
              onClick={connectZreader}
            >
              ⚡ Connect Zam Reader
            </button>
          )}

          {autoFillFailed && (
            <p className="pairing-autofill-hint">
              Zam Reader overlay not found on this page. Code copied — paste it
              in the Zam Reader TTS settings.
            </p>
          )}

          {/* Manual steps */}
          <ol className="pairing-steps">
            <li>Open Zam Reader on any page</li>
            <li>Click the speaker icon → TTS Settings → Local TTS</li>
            <li>Enter the code above and confirm</li>
          </ol>
        </>
      )}
    </div>
  );
}
