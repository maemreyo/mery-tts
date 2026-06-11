import { createMeryApiClient } from "@shared/api/meryApi";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

interface HealthPanelProps {
  token: string;
}

export function HealthPanel({ token }: HealthPanelProps) {
  const api = useMemo(() => createMeryApiClient({ token }), [token]);
  const query = useQuery({
    queryKey: ["health", token],
    queryFn: () => api.getHealth(),
    enabled: token.length > 0,
  });

  if (!token) {
    return (
      <section aria-label="Health">Enter a token to inspect health.</section>
    );
  }
  if (query.isLoading) {
    return <section aria-label="Health">Loading health...</section>;
  }
  if (query.isError) {
    return (
      <section aria-label="Health">
        Health unavailable. Check the local server.
      </section>
    );
  }

  const health = query.data;
  if (!health) {
    return (
      <section aria-label="Health">
        Health unavailable. Check the local server.
      </section>
    );
  }

  return (
    <section aria-label="Health">
      <h2>Health</h2>
      <p>Ready: {health.ready ? "yes" : "no"}</p>
      <p>Status: {health.health_status}</p>
      <p>Usable voices: {health.total_usable_voices}</p>
    </section>
  );
}
