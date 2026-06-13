import { NavigationProvider } from "@features/app-shell/NavigationContext";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type RenderOptions, render } from "@testing-library/react";
import type { RequestHandler } from "msw";
import type { ReactElement } from "react";
import { server } from "./handlers";

interface ProviderRenderOptions extends Omit<RenderOptions, "wrapper"> {
  handlers?: RequestHandler[];
}

export function renderWithProviders(
  ui: ReactElement,
  options?: ProviderRenderOptions,
) {
  const { handlers, ...renderOptions } = options ?? {};
  if (handlers?.length) {
    server.use(...handlers);
  }

  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
  return render(ui, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={client}>
        <NavigationProvider>{children}</NavigationProvider>
      </QueryClientProvider>
    ),
    ...renderOptions,
  });
}
