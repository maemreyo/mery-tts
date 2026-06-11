import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { PropsWithChildren } from "react";
import { describe, expect, it } from "vitest";
import { PlaygroundPanel } from "../PlaygroundPanel";

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  }
  return render(ui, { wrapper: Wrapper });
}

describe("PlaygroundPanel", () => {
  it("runs speech smoke through the backend wrapper", async () => {
    renderWithQuery(<PlaygroundPanel token="test-token" />);

    await userEvent.type(screen.getByLabelText("Voice model id"), "pack.en-us");
    await userEvent.click(
      screen.getByRole("button", { name: "Run speech smoke" }),
    );

    await waitFor(() =>
      expect(screen.getByText("Speech smoke succeeded.")).toBeInTheDocument(),
    );
  });
});
