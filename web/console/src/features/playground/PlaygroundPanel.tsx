import { zodResolver } from "@hookform/resolvers/zod";
import { createMeryApiClient } from "@shared/api/meryApi";
import { Button } from "@shared/ui/Button";
import { FormField } from "@shared/ui/FormField";
import { useMutation } from "@tanstack/react-query";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

interface PlaygroundPanelProps {
  token: string;
}

const playgroundSchema = z.object({
  voice: z.string().trim().min(1, "Choose a voice model id before running smoke."),
});

type PlaygroundFormValues = z.infer<typeof playgroundSchema>;

function statusVariant(ok?: boolean, error?: boolean): string {
  if (ok)    return "badge badge--success";
  if (error) return "badge badge--error";
  return "";
}

export function PlaygroundPanel({ token }: PlaygroundPanelProps) {
  const api = useMemo(() => createMeryApiClient({ token }), [token]);
  const form = useForm<PlaygroundFormValues>({
    defaultValues: { voice: "" },
    resolver: zodResolver(playgroundSchema),
  });
  const smokeMutation = useMutation({
    mutationFn: (values: PlaygroundFormValues) => api.runSpeechSmoke(values.voice),
  });

  const isSuccess = smokeMutation.data?.ok === true;
  const isFailure = smokeMutation.isError || smokeMutation.data?.ok === false;

  let statusText = "Ready for backend speech smoke.";
  if (smokeMutation.isPending) statusText = "Requesting speech from backend…";
  else if (isSuccess)          statusText = "Speech smoke succeeded.";
  else if (isFailure)          statusText = "Speech smoke failed with backend error.";

  return (
    <section aria-label="Playground">
      <div className="page-header">
        <h2>Playground</h2>
        <p>Run a backend speech smoke to confirm end-to-end TTS is working.</p>
      </div>

      <div className="panel">
        <form
          className="playground-form"
          onSubmit={form.handleSubmit((values) => smokeMutation.mutate(values))}
        >
          <FormField
            label="Voice model id"
            placeholder="e.g. pack.en-us-libritts-high"
            error={form.formState.errors.voice?.message}
            {...form.register("voice")}
          />
          <Button type="submit" disabled={!token || smokeMutation.isPending} variant="primary">
            {smokeMutation.isPending ? "Running…" : "Run speech smoke"}
          </Button>
        </form>

        <output
          role="status"
          style={{ marginTop: 12, display: "block", fontSize: 13 }}
          className={smokeMutation.status !== "idle" ? statusVariant(isSuccess, isFailure) : ""}
        >
          {statusText}
        </output>
      </div>
    </section>
  );
}
