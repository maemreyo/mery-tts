type StatusLevel = "ready" | "degraded" | "blocked" | "unknown";

interface StatusDotProps {
  level: StatusLevel;
  pulse?: boolean;
  label?: string;
}

export function StatusDot({ level, pulse = false, label }: StatusDotProps) {
  const cls = [
    "status-dot",
    `status-dot--${level}`,
    pulse && level !== "unknown" ? "status-dot--pulse" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span
      role="img"
      aria-label={label ?? `Server status: ${level}`}
      className={cls}
    />
  );
}
