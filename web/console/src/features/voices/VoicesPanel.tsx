import { createMeryApiClient } from "@shared/api/meryApi";
import { t } from "@shared/i18n/messages";
import { Button } from "@shared/ui/Button";
import { ConfirmDialog } from "@shared/ui/ConfirmDialog";
import { FieldGroup, FormField } from "@shared/ui/FormField";
import { SelectField } from "@shared/ui/SelectField";
import { SkeletonTable } from "@shared/ui/Skeleton";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  type SortingState,
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useEffect, useMemo, useState } from "react";
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

const sortOptions = [
  { label: "Name", value: "name" },
  { label: "Engine", value: "engine" },
  { label: "Locale", value: "locale" },
] as const;

const columnHelper = createColumnHelper<VoiceViewModel>();

const columns = [
  columnHelper.accessor("title", {
    header: "Voice",
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor("engine", {
    header: "Engine",
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor("locales", {
    header: "Locales",
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor("governanceLabel", {
    header: "Governance",
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor("installedLabel", {
    header: "State",
    cell: (info) => info.getValue(),
  }),
];

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

function sortingForMode(sortMode: SortMode): SortingState {
  if (sortMode === "engine") {
    return [{ id: "engine", desc: false }];
  }
  if (sortMode === "locale") {
    return [{ id: "locales", desc: false }];
  }
  return [{ id: "title", desc: false }];
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
  useEffect(() => {
    if (
      installStatus === "succeeded" ||
      installStatus === "failed" ||
      installStatus === "cancelled"
    ) {
      void queryClient.invalidateQueries({ queryKey: ["voices", token] });
    }
  }, [installStatus, queryClient, token]);

  const voices = voicesQuery.data ?? [];
  const visibleVoices = voices.filter((voice) => {
    const query =
      `${voice.title} ${voice.engine} ${voice.locales} ${voice.governanceLabel}`.toLowerCase();
    return (
      query.includes(search.toLowerCase()) &&
      voice.locales.toLowerCase().includes(localeFilter.toLowerCase())
    );
  });

  const table = useReactTable({
    data: visibleVoices,
    columns,
    state: { sorting: sortingForMode(sortMode) },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
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
    <section aria-labelledby="voices-heading">
      <div className="page-header">
        <h2 id="voices-heading">{t("voicesHeading")}</h2>
        <p>Manage available voice models for local TTS synthesis.</p>
      </div>

      <div className="panel voice-grid">
        <FieldGroup>
          <FormField
            label={t("searchVoices")}
            value={search}
            onChange={(event) => setSearch(event.currentTarget.value)}
            placeholder="English Demo"
          />
          <FormField
            label={t("localeFilter")}
            value={localeFilter}
            onChange={(event) => setLocaleFilter(event.currentTarget.value)}
            placeholder="en-US, vi-VN"
          />
          <SelectField
            label={t("sortVoices")}
            options={[...sortOptions]}
            value={sortMode}
            onValueChange={setSortMode}
          />
        </FieldGroup>

        {installJobQuery.data && (
          <div>
            <span className={`badge ${installJobQuery.data.status === "succeeded" ? "badge--success" : installJobQuery.data.status === "failed" ? "badge--error" : "badge--neutral"}`}>
              {installStatusLabel(installJobQuery.data.status)}
            </span>
          </div>
        )}

        <output role="status" style={{ fontSize: 13, color: "var(--text-muted)" }}>
          {status}
        </output>
        {voicesQuery.isLoading ? (
          <SkeletonTable rows={6} />
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th key={header.id} scope="col">
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                      </th>
                    ))}
                    <th scope="col">Action</th>
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        data-label={String(cell.column.columnDef.header)}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                    <td data-label="Action">
                      {row.original.installable ? (
                        <ConfirmDialog
                          title="Confirm voice install"
                          description={`Install ${row.original.title} using backend model id ${row.original.modelId}.`}
                          onConfirm={() => installMutation.mutate(row.original)}
                        >
                          <Button type="button" variant="primary">
                            {t("installVoice")}
                          </Button>
                        </ConfirmDialog>
                      ) : (
                        <span className="badge badge--neutral">
                          {row.original.governanceStatus}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
