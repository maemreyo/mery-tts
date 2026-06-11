import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { PropsWithChildren } from "react";
import { describe, expect, it } from "vitest";
import { VoicesPanel } from "../VoicesPanel";

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

describe("VoicesPanel", () => {
  it("loads voices through MSW and filters them by locale", async () => {
    renderWithQuery(<VoicesPanel token="test-token" />);

    await waitFor(() =>
      expect(screen.getByText("English Demo")).toBeInTheDocument(),
    );
    expect(screen.getByText("Vietnamese Demo")).toBeInTheDocument();
    expect(screen.getByText("gated (reference)")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Locale filter"), "vi-VN");

    expect(screen.queryByText("English Demo")).not.toBeInTheDocument();
    expect(screen.getByText("Vietnamese Demo")).toBeInTheDocument();
  });

  it("supports search, sort, and install polling states", async () => {
    renderWithQuery(<VoicesPanel token="test-token" />);

    await waitFor(() =>
      expect(screen.getByText("Vietnamese Demo")).toBeInTheDocument(),
    );
    await userEvent.selectOptions(
      screen.getByLabelText("Sort voices"),
      "engine",
    );
    await userEvent.type(screen.getByLabelText("Search voices"), "Vietnamese");
    expect(screen.queryByText("English Demo")).not.toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", { name: "Install voice" }),
    );

    await waitFor(() =>
      expect(screen.getByText("Install succeeded.")).toBeInTheDocument(),
    );
  });

  it("does not load voices without a token", () => {
    renderWithQuery(<VoicesPanel token="" />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Enter a token to load voices.",
    );
    expect(screen.queryByText("English Demo")).not.toBeInTheDocument();
  });
});
