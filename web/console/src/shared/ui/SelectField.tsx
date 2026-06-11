import * as Label from "@radix-ui/react-label";
import * as Select from "@radix-ui/react-select";

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
      <Label.Root htmlFor={id}>{label}</Label.Root>
      <Select.Root
        value={value}
        onValueChange={(next) => onValueChange(next as TValue)}
      >
        <Select.Trigger aria-label={label} className="select-trigger" id={id}>
          <Select.Value />
        </Select.Trigger>
        <Select.Portal>
          <Select.Content className="select-content" position="popper">
            <Select.Viewport>
              {options.map((option) => (
                <Select.Item
                  className="select-item"
                  key={option.value}
                  value={option.value}
                >
                  <Select.ItemText>{option.label}</Select.ItemText>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
    </div>
  );
}
