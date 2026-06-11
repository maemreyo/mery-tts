import { Slot } from "@radix-ui/react-slot";
import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  variant?: "primary" | "secondary";
}

export function Button({
  asChild = false,
  children,
  className = "",
  variant = "secondary",
  ...props
}: PropsWithChildren<ButtonProps>) {
  const Component = asChild ? Slot : "button";
  return (
    <Component
      className={`button button-${variant} ${className}`.trim()}
      {...props}
    >
      {children}
    </Component>
  );
}
