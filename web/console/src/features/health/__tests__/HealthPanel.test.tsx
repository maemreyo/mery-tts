import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { describe, expect, it } from "vitest";
import { HealthPanel } from "../HealthPanel";

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  }
  return render(ui, { wrapper: Wrapper });
}

describe("HealthPanel", () => {
  it("renders backend-owned readiness data", async () => {
    renderWithQuery(<HealthPanel token="test-token" />);
    await waitFor(() =>
      expect(screen.getByText("Ready: yes")).toBeInTheDocument(),
    );
    expect(screen.getByText("Status: ok")).toBeInTheDocument();
  });
});
