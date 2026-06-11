import * as Label from "@radix-ui/react-label";
import type { InputHTMLAttributes, PropsWithChildren, ReactNode } from "react";

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: ReactNode;
}

export function FormField({ error, id, label, ...inputProps }: FormFieldProps) {
  const inputId =
    id ?? inputProps.name ?? label.toLowerCase().replaceAll(" ", "-");
  return (
    <div className="form-field">
      <Label.Root htmlFor={inputId}>{label}</Label.Root>
      <input id={inputId} aria-invalid={Boolean(error)} {...inputProps} />
      {error ? <p className="field-error">{error}</p> : null}
    </div>
  );
}

export function FieldGroup({ children }: PropsWithChildren) {
  return <div className="field-row">{children}</div>;
}
