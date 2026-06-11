import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { PropsWithChildren } from "react";
import { describe, expect, it } from "vitest";
import { AppShell } from "../AppShell";

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

describe("AppShell", () => {
  it("clears remembered token on logout", async () => {
    localStorage.setItem("mery.console.authToken", "remembered-token");

    renderWithQuery(<AppShell />);

    expect(screen.getByLabelText("Bearer token")).toHaveValue(
      "remembered-token",
    );
    await userEvent.click(screen.getByRole("button", { name: "Log out" }));

    expect(screen.getByLabelText("Bearer token")).toHaveValue("");
    expect(localStorage.getItem("mery.console.authToken")).toBeNull();
  });
});
