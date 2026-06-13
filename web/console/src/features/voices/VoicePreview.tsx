import { synthesizeSpeech } from "@api/generated/client";
import type { VoiceViewModel } from "@shared/api/voiceViewModels";
import { AudioPlayer } from "@shared/ui/AudioPlayer";
import { useMutation } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

interface VoicePreviewProps {
  token: string;
  voice: VoiceViewModel;
}

export function VoicePreview({ token, voice }: VoicePreviewProps) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioUrlRef = useRef(audioUrl);
  audioUrlRef.current = audioUrl;

  useEffect(() => {
    return () => {
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
    };
  }, []);

  const previewMutation = useMutation({
    mutationFn: () =>
      synthesizeSpeech(
        { token },
        {
          model: "tts-1",
          voice: voice.modelId,
          input: "Hello, this is a preview of the selected voice.",
          response_format: "wav",
        },
      ),
    onSuccess: (result) => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      setAudioUrl(result.audioUrl);
    },
  });

  if (previewMutation.isPending) {
    return <span style={{ fontSize: 12, color: "var(--text-muted)" }}>…</span>;
  }

  if (audioUrl) {
    return (
      <AudioPlayer
        src={audioUrl}
        label={`Preview: ${voice.displayLabel ?? voice.title}`}
        className="voice-preview-player"
      />
    );
  }

  return (
    <button
      type="button"
      className="preview-btn"
      onClick={() => previewMutation.mutate()}
      disabled={previewMutation.isPending}
    >
      ▶
    </button>
  );
}
