export interface SelectOption<TValue extends string> {
  label: string;
  value: TValue;
}

interface SelectFieldProps<TValue extends string> {
  label: string;
  options: SelectOption<TValue>[];
  value: TValue;
  onValueChange: (value: TValue) => void;
}

export function SelectField<TValue extends string>({
  label,
  onValueChange,
  options,
  value,
}: SelectFieldProps<TValue>) {
  const id = label.toLowerCase().replaceAll(" ", "-");
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <select
        aria-label={label}
        className="select-trigger"
        id={id}
        value={value}
        onChange={(event) => onValueChange(event.currentTarget.value as TValue)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
