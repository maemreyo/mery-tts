import type { SpeechMark } from "@api/generated/client";
import { useNavigation } from "@features/app-shell/NavigationContext";
import { useSessionActivity } from "@features/session/SessionActivity";
import { zodResolver } from "@hookform/resolvers/zod";
import { createMeryApiClient } from "@shared/api/meryApi";
import { QUERY_KEYS } from "@shared/api/queryKeys";
import { loadVoiceViewModels } from "@shared/api/voiceViewModels";
import { Button } from "@shared/ui/Button";
import { FormField } from "@shared/ui/FormField";
import { SelectField } from "@shared/ui/SelectField";
import { SwitchField } from "@shared/ui/SwitchField";
import { useMutation, useQuery } from "@tanstack/react-query";
import { memo, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

interface PlaygroundPanelProps {
  token: string;
}

const playgroundSchema = z.object({
  voiceOverride: z.string().trim(),
});

type PlaygroundFormValues = z.infer<typeof playgroundSchema>;

function PlaygroundPanelBase({ token }: PlaygroundPanelProps) {
  const api = useMemo(() => createMeryApiClient({ token }), [token]);
  const { navigate } = useNavigation();
  const { recordSmoke } = useSessionActivity();

  const voicesQuery = useQuery({
    queryKey: QUERY_KEYS.voices(token),
    queryFn: () => loadVoiceViewModels(api),
    enabled: Boolean(token),
  });
  const installedVoices = voicesQuery.data?.filter((v) => v.installed) ?? [];

  const [selectedVoiceId, setSelectedVoiceId] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showWordTimings, setShowWordTimings] = useState(false);
  const [validationError, setValidationError] = useState<string | undefined>();
  const [synthText, setSynthText] = useState(
    "The quick brown fox jumps over the lazy dog.",
  );
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Revoke object URL on cleanup to avoid memory leaks
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  // Auto-select the first installed voice when the list loads
  useEffect(() => {
    if (!selectedVoiceId && installedVoices.length > 0) {
      setSelectedVoiceId(installedVoices[0].modelId);
    }
  }, [installedVoices, selectedVoiceId]);

  const form = useForm<PlaygroundFormValues>({
    defaultValues: { voiceOverride: "" },
    resolver: zodResolver(playgroundSchema),
  });

  const rawOverride = form.watch("voiceOverride");
  const activeModelId =
    showAdvanced && rawOverride.trim() ? rawOverride.trim() : selectedVoiceId;

  const synthMutation = useMutation({
    mutationFn: (modelId: string) =>
      api.synthesize({
        model: "tts-1",
        voice: modelId,
        input: synthText,
        response_format: "wav",
      }),
    onSuccess: (result, modelId) => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      setAudioUrl(result.audioUrl);
      const voice = installedVoices.find((v) => v.modelId === modelId);
      recordSmoke({
        voiceId: modelId,
        voiceLabel: voice?.displayLabel ?? voice?.title ?? modelId,
        ok: true,
        timestamp: new Date().toISOString(),
      });
    },
    onError: (_error, modelId) => {
      const voice = installedVoices.find((v) => v.modelId === modelId);
      recordSmoke({
        voiceId: modelId,
        voiceLabel: voice?.displayLabel ?? voice?.title ?? modelId,
        ok: false,
        timestamp: new Date().toISOString(),
      });
    },
  });

  const annotatedMutation = useMutation({
    mutationFn: (modelId: string) =>
      api.getAnnotatedSpeech({
        model: "tts-1",
        voice: modelId,
        input: synthText,
      }),
    onSuccess: (result) => {
      const bytes = Uint8Array.from(atob(result.audio_b64), (c) =>
        c.charCodeAt(0),
      );
      const blob = new Blob([bytes], { type: "audio/wav" });
      const newUrl = URL.createObjectURL(blob);
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      setAudioUrl(newUrl);
    },
  });

  const activeMutation = showWordTimings ? annotatedMutation : synthMutation;

  const wordMarks: SpeechMark[] =
    showWordTimings && annotatedMutation.isSuccess
      ? (annotatedMutation.data?.marks ?? [])
      : [];

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!synthText.trim()) {
      setValidationError("Enter some text to synthesize.");
      return;
    }
    if (!activeModelId) {
      setValidationError(
        showAdvanced
          ? "Enter an override model ID or select a voice above."
          : "Choose a voice before synthesizing.",
      );
      return;
    }
    setValidationError(undefined);
    if (showWordTimings) {
      annotatedMutation.mutate(activeModelId);
    } else {
      synthMutation.mutate(activeModelId);
    }
  }

  // No token state
  if (!token) {
    return (
      <section aria-label="Playground">
        <div className="page-header">
          <h2>TTS Workbench</h2>
          <p>Synthesize speech and preview voice output.</p>
        </div>
        <div className="panel">
          <p>Enter a bearer token to use the Playground.</p>
        </div>
      </section>
    );
  }

  // No installed voices state
  if (voicesQuery.isSuccess && installedVoices.length === 0) {
    return (
      <section aria-label="Playground">
        <div className="page-header">
          <h2>TTS Workbench</h2>
          <p>Synthesize speech and preview voice output.</p>
        </div>
        <div className="panel">
          <p>No installed voices found.</p>
          <button
            type="button"
            className="link-button"
            onClick={() => navigate("voices")}
          >
            Install a voice →
          </button>
        </div>
      </section>
    );
  }

  const showOutput = Boolean(audioUrl) || activeMutation.isError;

  return (
    <section aria-label="Playground">
      <div className="page-header">
        <h2>TTS Workbench</h2>
        <p>Synthesize speech and preview voice output.</p>
      </div>

      <div className="panel workbench-panel">
        <form className="workbench-input" onSubmit={handleSubmit}>
          {voicesQuery.isLoading ? (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
              Loading voices…
            </p>
          ) : (
            <SelectField
              label="Voice"
              placeholder="Select an installed voice…"
              value={selectedVoiceId}
              onValueChange={setSelectedVoiceId}
              options={installedVoices.map((v) => ({
                value: v.modelId,
                label: v.displayLabel ?? v.title,
              }))}
            />
          )}

          <div className="form-field">
            <label htmlFor="synth-text">Text to synthesize</label>
            <textarea
              id="synth-text"
              className="synth-textarea"
              rows={4}
              value={synthText}
              onChange={(e) => setSynthText(e.target.value)}
            />
          </div>

          <div className="workbench-controls">
            <Button
              type="submit"
              disabled={
                activeMutation.isPending || !activeModelId || !synthText.trim()
              }
              variant="primary"
            >
              {activeMutation.isPending ? "Synthesizing…" : "▶  Synthesize"}
            </Button>

            {installedVoices.length > 0 && (
              <SwitchField
                checked={showWordTimings}
                label="Word timings"
                onCheckedChange={setShowWordTimings}
              />
            )}
          </div>

          {validationError && (
            <p role="alert" className="field-error">
              {validationError}
            </p>
          )}
        </form>

        {showOutput && (
          <div className="workbench-output">
            <span className="workbench-output-label">Output</span>

            {audioUrl && (
              // biome-ignore lint/a11y/useMediaCaption: dynamically synthesized speech has no caption track
              <audio controls autoPlay src={audioUrl} className="synth-audio" />
            )}

            {showWordTimings &&
              annotatedMutation.isSuccess &&
              wordMarks.length > 0 && (
                <div className="word-marks" aria-label="Word timings">
                  {wordMarks.map((mark, i) => (
                    <span
                      key={`${mark.start_ms}-${mark.end_ms}-${i}`}
                      className="word-mark"
                      title={`${mark.start_ms}–${mark.end_ms}ms`}
                    >
                      {mark.word}
                    </span>
                  ))}
                </div>
              )}

            {activeMutation.isError && (
              <p className="workbench-error">
                Synthesis failed. Check that the voice is installed and the
                backend is reachable.
              </p>
            )}
          </div>
        )}

        <div className="advanced-disclosure">
          <button
            type="button"
            aria-expanded={showAdvanced}
            onClick={() => setShowAdvanced((prev) => !prev)}
            className="disclosure-toggle"
          >
            Advanced
          </button>
          {showAdvanced && (
            <div className="advanced-content">
              <FormField
                label="Override model ID"
                id="voice-override"
                placeholder="pack.en-us-libritts-high"
                error={undefined}
                {...form.register("voiceOverride")}
              />
              <p className="field-hint">Overrides the selected voice above</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export const PlaygroundPanel = memo(PlaygroundPanelBase);
