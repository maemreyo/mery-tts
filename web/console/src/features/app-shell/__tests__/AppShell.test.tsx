import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { AppShell } from "../AppShell";

describe("AppShell", () => {
  it("clears remembered token on logout", async () => {
    localStorage.setItem("mery.console.authToken", "remembered-token");

    renderWithProviders(<AppShell />);

    await userEvent.click(
      await screen.findByRole("button", { name: /log out/i }),
    );

    expect(localStorage.getItem("mery.console.authToken")).toBeNull();
  });
});
