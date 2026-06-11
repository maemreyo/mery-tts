import { createMeryApiClient } from "@shared/api/meryApi";
import { t } from "@shared/i18n/messages";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import type { VoiceViewModel } from "./voicesApi";
import {
  loadVoiceViewModels,
  pollVoiceInstall,
  startVoiceInstall,
} from "./voicesApi";

interface VoicesPanelProps {
  token: string;
}

type SortMode = "name" | "engine" | "locale";

function installStatusLabel(status: string): string {
  switch (status) {
    case "queued":
      return t("installQueued");
    case "running":
      return t("installRunning");
    case "succeeded":
      return t("installSucceeded");
    case "failed":
    case "cancelled":
      return t("installFailed");
    default:
      return status;
  }
}

export function VoicesPanel({ token }: VoicesPanelProps) {
  const [localeFilter, setLocaleFilter] = useState("");
  const [search, setSearch] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("name");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const api = useMemo(() => createMeryApiClient({ token }), [token]);

  const voicesQuery = useQuery({
    queryKey: ["voices", token],
    queryFn: () => loadVoiceViewModels(api),
    enabled: token.length > 0,
  });

  const installMutation = useMutation({
    mutationFn: (voice: VoiceViewModel) =>
      startVoiceInstall(api, voice.modelId),
    onSuccess: (job) => setActiveJobId(job.job_id),
  });

  const installJobQuery = useQuery({
    queryKey: ["install-job", activeJobId, token],
    queryFn: () => pollVoiceInstall(api, activeJobId ?? ""),
    enabled: Boolean(activeJobId && token),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 1000 : false;
    },
  });

  const installStatus = installJobQuery.data?.status;
  if (
    installStatus === "succeeded" ||
    installStatus === "failed" ||
    installStatus === "cancelled"
  ) {
    void queryClient.invalidateQueries({ queryKey: ["voices", token] });
  }

  const voices = voicesQuery.data ?? [];
  const visibleVoices = voices
    .filter((voice) => {
      const query =
        `${voice.title} ${voice.engine} ${voice.locales}`.toLowerCase();
      return (
        query.includes(search.toLowerCase()) &&
        voice.locales.toLowerCase().includes(localeFilter.toLowerCase())
      );
    })
    .sort((a, b) => {
      if (sortMode === "engine") {
        return a.engine.localeCompare(b.engine);
      }
      if (sortMode === "locale") {
        return a.locales.localeCompare(b.locales);
      }
      return a.title.localeCompare(b.title);
    });

  let status = t("enterToken");
  if (token && voicesQuery.isLoading) {
    status = t("loadingVoices");
  } else if (voicesQuery.isError) {
    status = t("loadVoicesError");
  } else if (token && voices.length === 0) {
    status = t("noVoices");
  } else if (token) {
    status = `${voices.length} voice options loaded.`;
  }

  return (
    <section aria-labelledby="voices-heading" className="voice-grid">
      <h2 id="voices-heading">{t("voicesHeading")}</h2>
      <div className="field-row">
        <label>
          {t("searchVoices")}
          <input
            aria-label={t("searchVoices")}
            value={search}
            onChange={(event) => setSearch(event.currentTarget.value)}
            placeholder="English Demo"
          />
        </label>
        <label>
          {t("localeFilter")}
          <input
            aria-label={t("localeFilter")}
            value={localeFilter}
            onChange={(event) => setLocaleFilter(event.currentTarget.value)}
            placeholder="en-US, vi-VN"
          />
        </label>
        <label>
          {t("sortVoices")}
          <select
            aria-label={t("sortVoices")}
            value={sortMode}
            onChange={(event) =>
              setSortMode(event.currentTarget.value as SortMode)
            }
          >
            <option value="name">Name</option>
            <option value="engine">Engine</option>
            <option value="locale">Locale</option>
          </select>
        </label>
      </div>
      <output>{status}</output>
      {installJobQuery.data ? (
        <output>{installStatusLabel(installJobQuery.data.status)}</output>
      ) : null}
      {visibleVoices.map((voice) => (
        <article className="voice-card" key={voice.id}>
          <h3>{voice.title}</h3>
          <p>
            <span className="badge">{voice.installedLabel}</span>
            <span className="badge">{voice.governanceLabel}</span>
          </p>
          <p>Engine: {voice.engine}</p>
          <p>Locales: {voice.locales}</p>
          {!voice.installed ? (
            <button type="button" onClick={() => installMutation.mutate(voice)}>
              {t("installVoice")}
            </button>
          ) : null}
        </article>
      ))}
    </section>
  );
}
