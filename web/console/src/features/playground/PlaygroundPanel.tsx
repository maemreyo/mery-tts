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

function statusVariant(ok?: boolean, error?: boolean): string {
  if (ok) return "badge badge--success";
  if (error) return "badge badge--error";
  return "";
}

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

  // Auto-select the first installed voice when the list loads so the user
  // can immediately click "Run smoke test" without an extra interaction.
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

  const smokeMutation = useMutation({
    mutationFn: (modelId: string) => api.runSpeechSmoke(modelId),
    onSettled: (data, _error, modelId) => {
      const voice = installedVoices.find((v) => v.modelId === modelId);
      recordSmoke({
        voiceId: modelId,
        voiceLabel: voice?.displayLabel ?? voice?.title ?? modelId,
        ok: data?.ok === true,
        timestamp: new Date().toISOString(),
      });
    },
  });

  const annotatedMutation = useMutation({
    mutationFn: (modelId: string) =>
      api.getAnnotatedSpeech({
        model: "tts-1",
        voice: modelId,
        input: "Console smoke",
      }),
    onSettled: (data, _error, modelId) => {
      const voice = installedVoices.find((v) => v.modelId === modelId);
      recordSmoke({
        voiceId: modelId,
        voiceLabel: voice?.displayLabel ?? voice?.title ?? modelId,
        ok: data?.marks_available === true,
        timestamp: new Date().toISOString(),
      });
    },
  });

  const activeMutation = showWordTimings ? annotatedMutation : smokeMutation;

  const isSuccess = showWordTimings
    ? annotatedMutation.isSuccess
    : smokeMutation.data?.ok === true;
  const isFailure = showWordTimings
    ? annotatedMutation.isError
    : smokeMutation.isError || smokeMutation.data?.ok === false;

  let statusText = "Ready for backend speech smoke.";
  if (activeMutation.isPending) statusText = "Requesting speech from backend…";
  else if (isSuccess) statusText = "Speech smoke succeeded.";
  else if (isFailure)
    statusText =
      "Speech smoke failed. The voice may not be ready — check Health for engine status.";

  const wordMarks: SpeechMark[] =
    showWordTimings && annotatedMutation.isSuccess
      ? (annotatedMutation.data?.marks ?? [])
      : [];
  const marksAvailable =
    showWordTimings && annotatedMutation.isSuccess
      ? annotatedMutation.data?.marks_available
      : undefined;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!activeModelId) {
      setValidationError(
        showAdvanced
          ? "Enter an override model ID or select a voice above."
          : "Choose a voice before running smoke.",
      );
      return;
    }
    setValidationError(undefined);
    if (showWordTimings) {
      annotatedMutation.mutate(activeModelId);
    } else {
      smokeMutation.mutate(activeModelId);
    }
  }

  // No token state
  if (!token) {
    return (
      <section aria-label="Playground">
        <div className="page-header">
          <h2>Playground</h2>
          <p>
            Run a backend speech smoke to confirm end-to-end TTS is working.
          </p>
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
          <h2>Playground</h2>
          <p>
            Run a backend speech smoke to confirm end-to-end TTS is working.
          </p>
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

  return (
    <section aria-label="Playground">
      <div className="page-header">
        <h2>Playground</h2>
        <p>Run a backend speech smoke to confirm end-to-end TTS is working.</p>
      </div>

      <div className="panel">
        <form className="playground-form" onSubmit={handleSubmit}>
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

          {installedVoices.length > 0 && (
            <SwitchField
              checked={showWordTimings}
              label="Show word timings"
              onCheckedChange={setShowWordTimings}
            />
          )}

          <div className="advanced-disclosure">
            <button
              type="button"
              aria-expanded={showAdvanced}
              onClick={() => setShowAdvanced((prev) => !prev)}
              className="disclosure-toggle"
            >
              Advanced options
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

          {validationError && (
            <p role="alert" className="field-error">
              {validationError}
            </p>
          )}

          <Button
            type="submit"
            disabled={activeMutation.isPending}
            variant="primary"
          >
            {activeMutation.isPending ? "Running…" : "Run speech smoke"}
          </Button>
        </form>

        <output
          aria-live="polite"
          style={{ marginTop: 12, display: "block", fontSize: 13 }}
          className={
            activeMutation.status !== "idle"
              ? statusVariant(isSuccess, isFailure)
              : ""
          }
        >
          {statusText}
        </output>

        {showWordTimings && annotatedMutation.isSuccess && (
          <>
            {marksAvailable === false && (
              <p className="word-marks-unavailable">
                This voice does not support word timings.
              </p>
            )}
            {wordMarks.length > 0 && (
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
          </>
        )}
      </div>
    </section>
  );
}

export const PlaygroundPanel = memo(PlaygroundPanelBase);
