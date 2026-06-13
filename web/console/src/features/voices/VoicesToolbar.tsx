import { t } from "@shared/i18n/messages";
import { FieldGroup, FormField } from "@shared/ui/FormField";
import { SelectField } from "@shared/ui/SelectField";
import type { SortMode } from "./useVoices";

const sortOptions = [
  { label: "Name", value: "name" },
  { label: "Engine", value: "engine" },
  { label: "Locale", value: "locale" },
] as const;

interface VoicesToolbarProps {
  search: string;
  onSearchChange: (v: string) => void;
  localeFilter: string;
  onLocaleFilterChange: (v: string) => void;
  sortMode: SortMode;
  onSortModeChange: (v: SortMode) => void;
}

export function VoicesToolbar({
  search,
  onSearchChange,
  localeFilter,
  onLocaleFilterChange,
  sortMode,
  onSortModeChange,
}: VoicesToolbarProps) {
  return (
    <FieldGroup>
      <FormField
        label={t("searchVoices")}
        value={search}
        onChange={(event) => onSearchChange(event.currentTarget.value)}
        placeholder="English Demo"
      />
      <FormField
        label={t("localeFilter")}
        value={localeFilter}
        onChange={(event) => onLocaleFilterChange(event.currentTarget.value)}
        placeholder="en-US, vi-VN"
      />
      <SelectField
        label={t("sortVoices")}
        options={[...sortOptions]}
        value={sortMode}
        onValueChange={onSortModeChange}
      />
    </FieldGroup>
  );
}
