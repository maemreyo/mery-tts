import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { PropsWithChildren } from "react";
import { describe, expect, it } from "vitest";
import { AppShell } from "../AppShell";
import { createConsoleRouteTree } from "../routes";

async function renderWithProviders() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const router = createRouter({ routeTree: createConsoleRouteTree(AppShell) });
  await router.load();
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
  }
  return render(<RouterProvider router={router} />, {
    wrapper: Wrapper,
  });
}

describe("AppShell", () => {
  it("clears remembered token on logout", async () => {
    localStorage.setItem("mery.console.authToken", "remembered-token");

    await renderWithProviders();

    expect(await screen.findByLabelText("Bearer token")).toHaveValue(
      "remembered-token",
    );
    await userEvent.click(screen.getByRole("button", { name: "Log out" }));

    expect(screen.getByLabelText("Bearer token")).toHaveValue("");
    expect(localStorage.getItem("mery.console.authToken")).toBeNull();
  });
});
