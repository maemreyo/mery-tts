import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { DeveloperPanel } from "../DeveloperPanel";

describe("DeveloperPanel", () => {
  it("keeps debug payloads opt-in and sanitized", async () => {
    render(<DeveloperPanel />);
    expect(screen.queryByText(/raw private text/i)).not.toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Show Developer Mode" }),
    );
    expect(
      screen.getByText(/Pull-based diagnostics only/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/must stay redacted/i)).toBeInTheDocument();
  });
});
