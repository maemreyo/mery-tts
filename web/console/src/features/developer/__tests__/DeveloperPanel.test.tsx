import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { DeveloperPanel } from "../DeveloperPanel";

describe("DeveloperPanel", () => {
  it("keeps debug payloads opt-in — panel is hidden by default", () => {
    renderWithProviders(<DeveloperPanel />);
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText("Sanitized diagnostic payload example"),
    ).not.toBeInTheDocument();
  });

  it("shows the Preview only notice when developer tools are enabled", async () => {
    renderWithProviders(<DeveloperPanel />);
    await userEvent.click(
      screen.getByRole("button", { name: "Developer tools" }),
    );
    const notice = screen.getByRole("note");
    expect(notice).toBeInTheDocument();
    expect(notice).toHaveTextContent(/Preview only/i);
    expect(notice).toHaveTextContent(
      /Live diagnostics are not connected in v1/i,
    );
  });

  it("does not expose bearer tokens or raw private text in rendered output", async () => {
    renderWithProviders(<DeveloperPanel />);
    await userEvent.click(
      screen.getByRole("button", { name: "Developer tools" }),
    );
    // The pre element should list "bearer_token" only as a redacted field name, not as a value
    const pre = screen.getByLabelText("Sanitized diagnostic payload example");
    expect(pre).toBeInTheDocument();
    // Confirm the payload is sanitized (redacted array is present, no actual secret values)
    expect(pre.textContent).toContain('"bearer_token"');
    expect(pre.textContent).toContain('"sanitized": true');
    // No actual token values should appear
    expect(pre.textContent).not.toMatch(/Bearer\s+[A-Za-z0-9._-]{10,}/);
  });

  it("renders the Overview navigation button when developer tools are enabled", async () => {
    renderWithProviders(<DeveloperPanel />);
    await userEvent.click(
      screen.getByRole("button", { name: "Developer tools" }),
    );
    const btn = screen.getByRole("button", { name: /← Overview/i });
    expect(btn).toBeInTheDocument();
  });

  it("has correct aria-pressed attribute on the toggle button", async () => {
    renderWithProviders(<DeveloperPanel />);
    const btn = screen.getByRole("button", { name: "Developer tools" });
    expect(btn).toHaveAttribute("aria-pressed", "false");
    await userEvent.click(btn);
    expect(
      screen.getByRole("button", { name: "Hide developer tools" }),
    ).toHaveAttribute("aria-pressed", "true");
  });
});
