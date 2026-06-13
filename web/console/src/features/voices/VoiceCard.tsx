import type { VoiceViewModel } from "@shared/api/voiceViewModels";
import { t } from "@shared/i18n/messages";
import { Button } from "@shared/ui/Button";
import { ConfirmDialog } from "@shared/ui/ConfirmDialog";

interface VoiceCardProps {
  voice: VoiceViewModel;
  onInstall: (v: VoiceViewModel) => void;
}

export function VoiceCard({ voice, onInstall }: VoiceCardProps) {
  return (
    <article className="voice-card" aria-label={voice.title}>
      <div className="voice-card-name">{voice.title}</div>
      <div className="voice-card-meta">
        {voice.engine} &middot; {voice.locales}
      </div>
      <div className="voice-card-actions">
        <span
          className={`badge ${
            voice.installed ? "badge--success" : "badge--neutral"
          }`}
        >
          {voice.installedLabel}
        </span>
        <span className="badge badge--neutral">{voice.governanceLabel}</span>
        {voice.installable ? (
          <ConfirmDialog
            title="Confirm voice install"
            description={`Install ${voice.title} using backend model id ${voice.modelId}.`}
            onConfirm={() => onInstall(voice)}
          >
            <Button type="button" variant="primary">
              {t("installVoice")}
            </Button>
          </ConfirmDialog>
        ) : (
          <span className="badge badge--neutral">{voice.governanceStatus}</span>
        )}
      </div>
    </article>
  );
}
