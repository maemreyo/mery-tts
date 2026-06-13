export interface SelectOption<TValue extends string> {
  label: string;
  value: TValue;
}

interface SelectFieldProps<TValue extends string> {
  label: string;
  options: SelectOption<TValue>[];
  value: TValue | "";
  onValueChange: (value: TValue) => void;
  /** Shown as a disabled first option when value is empty. */
  placeholder?: string;
}

export function SelectField<TValue extends string>({
  label,
  onValueChange,
  options,
  value,
  placeholder,
}: SelectFieldProps<TValue>) {
  const id = label.toLowerCase().replaceAll(" ", "-");
  const showPlaceholder = value === "" || value === undefined;
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <select
        aria-label={label}
        className="select-trigger"
        id={id}
        value={value}
        onChange={(event) => {
          const next = event.currentTarget.value;
          if (next) onValueChange(next as TValue);
        }}
      >
        {showPlaceholder && (
          <option value="" disabled>
            {placeholder ?? `Choose ${label.toLowerCase()}…`}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
