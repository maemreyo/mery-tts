import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ConnectionCard } from "../ConnectionCard";

describe("ConnectionCard", () => {
  it("renders bearer token input and buttons", () => {
    render(<ConnectionCard onSubmit={vi.fn()} onLogout={vi.fn()} />);
    expect(screen.getByLabelText("Bearer token")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Use token" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Log out" })).toBeInTheDocument();
  });

  it("calls onSubmit with token and remember values on submit", async () => {
    const onSubmit = vi.fn();
    render(<ConnectionCard onSubmit={onSubmit} onLogout={vi.fn()} />);
    await userEvent.type(screen.getByLabelText("Bearer token"), "my-token");
    await userEvent.click(screen.getByRole("button", { name: "Use token" }));
    expect(onSubmit).toHaveBeenCalledWith("my-token", false);
  });

  it("calls onLogout when Log out button is clicked", async () => {
    const onLogout = vi.fn();
    render(<ConnectionCard onSubmit={vi.fn()} onLogout={onLogout} />);
    await userEvent.click(screen.getByRole("button", { name: "Log out" }));
    expect(onLogout).toHaveBeenCalledOnce();
  });

  it("shows validation error for tokens exceeding max length", async () => {
    const onSubmit = vi.fn();
    render(<ConnectionCard onSubmit={onSubmit} onLogout={vi.fn()} />);
    const longToken = "a".repeat(4097);
    // Use fireEvent.change to avoid the per-keystroke overhead of userEvent.type
    fireEvent.change(screen.getByLabelText("Bearer token"), {
      target: { value: longToken },
    });
    await userEvent.click(screen.getByRole("button", { name: "Use token" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("populates form fields from currentToken and currentRemember props", () => {
    render(
      <ConnectionCard
        onSubmit={vi.fn()}
        onLogout={vi.fn()}
        currentToken="prefilled-token"
        currentRemember={false}
      />,
    );
    expect(screen.getByLabelText("Bearer token")).toHaveValue(
      "prefilled-token",
    );
  });
});
