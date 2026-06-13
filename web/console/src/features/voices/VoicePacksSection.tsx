import type { VoicePackSummary } from "@api/generated/client";
import { createMeryApiClient } from "@shared/api/meryApi";
import { QUERY_KEYS } from "@shared/api/queryKeys";
import { Button } from "@shared/ui/Button";
import { ConfirmDialog } from "@shared/ui/ConfirmDialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

interface VoicePacksSectionProps {
  token: string;
}

function statusBadgeClass(status: VoicePackSummary["status"]): string {
  switch (status) {
    case "installed":
      return "badge--success";
    case "partial":
      return "badge--warning";
    case "missing_runtime":
      return "badge--error";
    default:
      return "badge--neutral";
  }
}

function formatMB(bytes: number): string {
  return `${(bytes / 1_048_576).toFixed(1)} MB`;
}

export function VoicePacksSection({ token }: VoicePacksSectionProps) {
  const queryClient = useQueryClient();
  const api = useMemo(() => createMeryApiClient({ token }), [token]);

  const packsQuery = useQuery({
    queryKey: QUERY_KEYS.voicePacks(token),
    queryFn: () => api.getVoicePacks(),
    enabled: Boolean(token),
  });

  const installMutation = useMutation({
    mutationFn: (voicePackId: string) => api.installVoicePack(voicePackId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.voices(token),
      });
    },
  });

  const packs = packsQuery.data?.voice_packs ?? [];

  if (packs.length === 0) {
    return null;
  }

  return (
    <div className="voice-packs-section">
      <h3>Voice Packs</h3>
      <div className="voice-pack-grid">
        {packs.map((pack) => (
          <div key={pack.voice_pack_id} className="voice-pack-card">
            <div className="voice-pack-name">{pack.display_name}</div>
            <div className="voice-pack-desc">{pack.description}</div>
            <div className="voice-pack-meta">
              <span className={`badge ${statusBadgeClass(pack.status)}`}>
                {pack.status}
              </span>
              <span>
                {pack.voices_installed}/{pack.voices_total} voices
              </span>
              <span>{formatMB(pack.estimated_size_bytes)}</span>
            </div>
            {pack.status !== "installed" && pack.runtimes_ready && (
              <div className="voice-pack-action">
                <ConfirmDialog
                  title="Confirm pack install"
                  description={`Install the "${pack.display_name}" voice pack (${pack.voices_total} voices, ~${formatMB(pack.estimated_size_bytes)}).`}
                  onConfirm={() => installMutation.mutate(pack.voice_pack_id)}
                >
                  <Button type="button" variant="primary">
                    Install pack
                  </Button>
                </ConfirmDialog>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
