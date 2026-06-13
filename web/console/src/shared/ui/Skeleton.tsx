interface SkeletonProps {
  variant?: "line" | "line-sm" | "line-lg" | "row";
  width?: string;
  className?: string;
}

export function Skeleton({
  variant = "line",
  width,
  className = "",
}: SkeletonProps) {
  const variantClass =
    variant === "row"
      ? "skeleton skeleton-row"
      : variant === "line-sm"
        ? "skeleton skeleton-line skeleton-line--sm"
        : variant === "line-lg"
          ? "skeleton skeleton-line skeleton-line--lg"
          : "skeleton skeleton-line";
  return (
    <div
      aria-hidden="true"
      className={`${variantClass} ${className}`}
      style={width ? { width } : undefined}
    />
  );
}

interface SkeletonTableProps {
  rows?: number;
  cols?: number;
}

export function SkeletonTable({ rows = 5, cols = 5 }: SkeletonTableProps) {
  return (
    <div aria-busy="true" aria-label="Loading…">
      {Array.from({ length: rows }, (_, i) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: skeleton rows are static placeholders with no identity
        <div key={i} className="skeleton skeleton-row" />
      ))}
    </div>
  );
}
