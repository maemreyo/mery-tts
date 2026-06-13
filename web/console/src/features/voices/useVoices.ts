import { createMeryApiClient } from "@shared/api/meryApi";
import { QUERY_KEYS } from "@shared/api/queryKeys";
import {
  type VoiceViewModel,
  loadVoiceViewModels,
  pollVoiceInstall,
  startVoiceInstall,
} from "@shared/api/voiceViewModels";
import { t } from "@shared/i18n/messages";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

export type SortMode = "name" | "engine" | "locale";

export interface UseVoicesResult {
  voices: VoiceViewModel[];
  visibleVoices: VoiceViewModel[];
  isLoading: boolean;
  isError: boolean;
  search: string;
  setSearch: (v: string) => void;
  localeFilter: string;
  setLocaleFilter: (v: string) => void;
  sortMode: SortMode;
  setSortMode: (v: SortMode) => void;
  installStatus: string | undefined;
  installVoice: (voice: VoiceViewModel) => void;
  uninstallVoice: (voice: VoiceViewModel) => void;
  installJobStatus: string | undefined;
  statusText: string;
}

export function useVoices({ token }: { token: string }): UseVoicesResult {
  const [localeFilter, setLocaleFilter] = useState("");
  const [search, setSearch] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("name");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const api = useMemo(() => createMeryApiClient({ token }), [token]);

  const voicesQuery = useQuery({
    queryKey: QUERY_KEYS.voices(token),
    queryFn: () => loadVoiceViewModels(api),
    enabled: token.length > 0,
  });

  const installMutation = useMutation({
    mutationFn: (voice: VoiceViewModel) =>
      startVoiceInstall(api, voice.modelId),
    onSuccess: (job) => setActiveJobId(job.job_id),
  });

  const uninstallMutation = useMutation({
    mutationFn: (voice: VoiceViewModel) => api.deleteVoice(voice.modelId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.voices(token),
      });
    },
  });

  const installJobQuery = useQuery({
    queryKey: QUERY_KEYS.installJob(activeJobId, token),
    queryFn: () => pollVoiceInstall(api, activeJobId ?? ""),
    enabled: Boolean(activeJobId && token),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 1000 : false;
    },
  });

  const installStatus = installJobQuery.data?.status;

  useEffect(() => {
    if (
      installStatus === "succeeded" ||
      installStatus === "failed" ||
      installStatus === "cancelled"
    ) {
      void queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.voices(token),
      });
    }
  }, [installStatus, queryClient, token]);

  const voices = voicesQuery.data ?? [];

  const visibleVoices = useMemo(() => {
    const searchLower = search.toLowerCase();
    const localeLower = localeFilter.toLowerCase();
    return voices.filter((voice) => {
      const text =
        `${voice.title} ${voice.engine} ${voice.locales} ${voice.governanceLabel}`.toLowerCase();
      return (
        text.includes(searchLower) &&
        voice.locales.toLowerCase().includes(localeLower)
      );
    });
  }, [voices, search, localeFilter]);

  let statusText = t("enterToken");
  if (token && voicesQuery.isLoading) {
    statusText = t("loadingVoices");
  } else if (voicesQuery.isError) {
    statusText = t("loadVoicesError");
  } else if (token && voices.length === 0) {
    statusText = t("noVoices");
  } else if (token && (search || localeFilter)) {
    statusText =
      visibleVoices.length === 0
        ? "No voices match the current filter."
        : `${visibleVoices.length} of ${voices.length} voices match filter.`;
  } else if (token) {
    statusText = `${voices.length} voice options loaded.`;
  }

  return {
    voices,
    visibleVoices,
    isLoading: voicesQuery.isLoading,
    isError: voicesQuery.isError,
    search,
    setSearch,
    localeFilter,
    setLocaleFilter,
    sortMode,
    setSortMode,
    installStatus,
    installVoice: installMutation.mutate,
    uninstallVoice: uninstallMutation.mutate,
    installJobStatus: installJobQuery.data?.status,
    statusText,
  };
}
