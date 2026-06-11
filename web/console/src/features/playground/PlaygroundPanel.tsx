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
  voice: z
    .string()
    .trim()
    .min(1, "Choose a voice model id before running smoke."),
});

type PlaygroundFormValues = z.infer<typeof playgroundSchema>;

export function PlaygroundPanel({ token }: PlaygroundPanelProps) {
  const api = useMemo(() => createMeryApiClient({ token }), [token]);
  const form = useForm<PlaygroundFormValues>({
    defaultValues: { voice: "" },
    resolver: zodResolver(playgroundSchema),
  });
  const smokeMutation = useMutation({
    mutationFn: (values: PlaygroundFormValues) =>
      api.runSpeechSmoke(values.voice),
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
      <form
        className="playground-form"
        onSubmit={form.handleSubmit((values) => smokeMutation.mutate(values))}
      >
        <FormField
          label="Voice model id"
          error={form.formState.errors.voice?.message}
          {...form.register("voice")}
        />
        <Button type="submit" disabled={!token} variant="primary">
          Run speech smoke
        </Button>
      </form>
      <output>{status}</output>
    </section>
  );
}
