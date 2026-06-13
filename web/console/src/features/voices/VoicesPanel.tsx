import type { VoiceViewModel } from "@shared/api/voiceViewModels";
import { t } from "@shared/i18n/messages";
import { Button } from "@shared/ui/Button";
import { ConfirmDialog } from "@shared/ui/ConfirmDialog";
import { SkeletonTable } from "@shared/ui/Skeleton";
import {
  type SortingState,
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { memo, useMemo } from "react";
import { VoiceCard } from "./VoiceCard";
import { VoicePacksSection } from "./VoicePacksSection";
import { VoicePreview } from "./VoicePreview";
import { VoicesToolbar } from "./VoicesToolbar";
import { useVoices } from "./useVoices";

interface VoicesPanelProps {
  token: string;
}

// Stable row model factories — created once at module load, not per render.
const coreRowModel = getCoreRowModel();
const sortedRowModel = getSortedRowModel();

const columnHelper = createColumnHelper<VoiceViewModel>();

const columns = [
  columnHelper.accessor("title", {
    header: "Voice",
    cell: (info) => info.row.original.displayLabel ?? info.getValue(),
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

function sortingForMode(sortMode: "name" | "engine" | "locale"): SortingState {
  if (sortMode === "engine") {
    return [{ id: "engine", desc: false }];
  }
  if (sortMode === "locale") {
    return [{ id: "locales", desc: false }];
  }
  return [{ id: "title", desc: false }];
}

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

function VoicesPanelBase({ token }: VoicesPanelProps) {
  const {
    visibleVoices,
    isLoading,
    search,
    setSearch,
    localeFilter,
    setLocaleFilter,
    sortMode,
    setSortMode,
    installVoice,
    uninstallVoice,
    installJobStatus,
    statusText,
  } = useVoices({ token });

  const sorting = useMemo(() => sortingForMode(sortMode), [sortMode]);

  const table = useReactTable({
    data: visibleVoices,
    columns,
    state: { sorting },
    getCoreRowModel: coreRowModel,
    getSortedRowModel: sortedRowModel,
  });

  return (
    <section aria-labelledby="voices-heading">
      <div className="page-header">
        <h2 id="voices-heading">{t("voicesHeading")}</h2>
        <p>Manage available voice models for local TTS synthesis.</p>
      </div>

      <div className="panel voice-grid">
        <VoicesToolbar
          search={search}
          onSearchChange={setSearch}
          localeFilter={localeFilter}
          onLocaleFilterChange={setLocaleFilter}
          sortMode={sortMode}
          onSortModeChange={setSortMode}
        />

        {installJobStatus && (
          <div className="install-status-row">
            <span
              className={`badge ${
                installJobStatus === "succeeded"
                  ? "badge--success"
                  : installJobStatus === "failed" ||
                      installJobStatus === "cancelled"
                    ? "badge--error"
                    : "badge--accent"
              }`}
            >
              {installStatusLabel(installJobStatus)}
            </span>
            {(installJobStatus === "failed" ||
              installJobStatus === "cancelled") && (
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                — check Developer tab for diagnostics, then try installing again
              </span>
            )}
          </div>
        )}

        <output className="voices-status" aria-live="polite">
          {statusText}
        </output>

        {isLoading ? (
          <SkeletonTable rows={6} />
        ) : (
          <>
            <div className="voices-desktop">
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
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext(),
                            )}
                          </td>
                        ))}
                        <td data-label="Action">
                          {row.original.installed ? (
                            <>
                              <ConfirmDialog
                                title="Confirm voice uninstall"
                                description={`Uninstall ${row.original.title}? This removes the model files from disk.`}
                                onConfirm={() => uninstallVoice(row.original)}
                              >
                                <Button type="button">Uninstall</Button>
                              </ConfirmDialog>
                              <VoicePreview
                                token={token}
                                voice={row.original}
                              />
                            </>
                          ) : row.original.installable ? (
                            <ConfirmDialog
                              title="Confirm voice install"
                              description={`Install ${row.original.title} (${row.original.modelId}).`}
                              onConfirm={() => installVoice(row.original)}
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
            </div>

            <div className="voices-mobile">
              {visibleVoices.map((voice) => (
                <VoiceCard
                  key={voice.id}
                  voice={voice}
                  token={token}
                  onInstall={installVoice}
                  onUninstall={uninstallVoice}
                />
              ))}
            </div>
          </>
        )}

        <VoicePacksSection token={token} />
      </div>
    </section>
  );
}

export const VoicesPanel = memo(VoicesPanelBase);
