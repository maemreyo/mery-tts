import { createMeryApiClient } from "@shared/api/meryApi";
import { QUERY_KEYS } from "@shared/api/queryKeys";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import type { ConnectionStatus } from "./types";
import { useSession } from "./useSession";

export function useConnection() {
  const { session, applyToken, logout } = useSession();
  const token = session.token;
  const api = useMemo(
    () => (token ? createMeryApiClient({ token }) : null),
    [token],
  );

  const healthQuery = useQuery({
    queryKey: QUERY_KEYS.health(token),
    queryFn: () => api?.getHealth(),
    enabled: Boolean(token && api),
    refetchInterval: 30_000,
    staleTime: 20_000,
  });

  let status: ConnectionStatus = "disconnected";
  if (token && healthQuery.isLoading) status = "checking";
  else if (token && healthQuery.isSuccess) status = "connected";
  else if (token && healthQuery.isError) status = "disconnected";

  return { token, remember: session.remember, status, applyToken, logout };
}
