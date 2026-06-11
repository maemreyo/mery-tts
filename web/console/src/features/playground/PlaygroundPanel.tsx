import { createMeryApiClient } from "@shared/api/meryApi";
import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";

interface PlaygroundPanelProps {
  token: string;
}

export function PlaygroundPanel({ token }: PlaygroundPanelProps) {
  const [voice, setVoice] = useState("");
  const api = useMemo(() => createMeryApiClient({ token }), [token]);
  const smokeMutation = useMutation({
    mutationFn: () => api.runSpeechSmoke(voice),
  });

  let status = "Ready for backend speech smoke.";
  if (smokeMutation.isPending) {
    status = "Requesting speech from backend...";
  } else if (smokeMutation.data?.ok) {
    status = "Speech smoke succeeded.";
  } else if (smokeMutation.isError || smokeMutation.data?.ok === false) {
    status = "Speech smoke failed with backend error.";
  }

  return (
    <section aria-label="Playground">
      <h2>Playground</h2>
      <label>
        Voice model id
        <input
          aria-label="Voice model id"
          value={voice}
          onChange={(event) => setVoice(event.currentTarget.value)}
        />
      </label>
      <button
        type="button"
        disabled={!token || !voice}
        onClick={() => smokeMutation.mutate()}
      >
        Run speech smoke
      </button>
      <output>{status}</output>
    </section>
  );
}
