import * as Label from "@radix-ui/react-label";
import * as Switch from "@radix-ui/react-switch";

interface SwitchFieldProps {
  checked: boolean;
  label: string;
  onCheckedChange: (checked: boolean) => void;
}

export function SwitchField({
  checked,
  label,
  onCheckedChange,
}: SwitchFieldProps) {
  const id = label.toLowerCase().replaceAll(" ", "-");
  return (
    <div className="switch-field">
      <Switch.Root
        checked={checked}
        className="switch-root"
        id={id}
        onCheckedChange={onCheckedChange}
      >
        <Switch.Thumb className="switch-thumb" />
      </Switch.Root>
      <Label.Root htmlFor={id}>{label}</Label.Root>
    </div>
  );
}
