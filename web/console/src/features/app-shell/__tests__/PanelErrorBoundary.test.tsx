import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { PanelErrorBoundary } from "../PanelErrorBoundary";

function Thrower(): never {
  throw new Error("render error");
}

describe("PanelErrorBoundary", () => {
  it("renders children when there is no error", () => {
    render(
      <PanelErrorBoundary sectionName="Voices" onGoToOverview={() => {}}>
        <p>Panel content</p>
      </PanelErrorBoundary>,
    );
    expect(screen.getByText("Panel content")).toBeInTheDocument();
  });

  it("renders fallback with role=alert when a child throws", () => {
    // Suppress the expected console.error from React's error boundary
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <PanelErrorBoundary sectionName="Voices" onGoToOverview={() => {}}>
        <Thrower />
      </PanelErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(
      screen.getByText("Something went wrong in Voices."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Go to Overview" }),
    ).toBeInTheDocument();

    spy.mockRestore();
  });

  it("does not expose the raw error message in the fallback UI", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <PanelErrorBoundary sectionName="Voices" onGoToOverview={() => {}}>
        <Thrower />
      </PanelErrorBoundary>,
    );

    expect(screen.queryByText(/render error/i)).not.toBeInTheDocument();

    spy.mockRestore();
  });

  it("calls onGoToOverview when the button is clicked", async () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    const onGoToOverview = vi.fn();

    render(
      <PanelErrorBoundary sectionName="Voices" onGoToOverview={onGoToOverview}>
        <Thrower />
      </PanelErrorBoundary>,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Go to Overview" }),
    );
    expect(onGoToOverview).toHaveBeenCalledOnce();

    spy.mockRestore();
  });
});
