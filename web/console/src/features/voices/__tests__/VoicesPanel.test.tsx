import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { VoicesPanel } from "../VoicesPanel";

describe("VoicesPanel", () => {
  it("loads voices through MSW and filters them by locale", async () => {
    renderWithProviders(<VoicesPanel token="test-token" />);

    await waitFor(() =>
      expect(screen.getAllByText("English Demo").length).toBeGreaterThan(0),
    );
    expect(screen.getAllByText("Vietnamese Demo").length).toBeGreaterThan(0);
    expect(screen.getAllByText("French Demo").length).toBeGreaterThan(0);
    expect(screen.getAllByText("gated (reference)").length).toBeGreaterThan(0);

    await userEvent.type(screen.getByLabelText("Locale filter"), "vi-VN");

    expect(screen.queryAllByText("English Demo")).toHaveLength(0);
    expect(screen.getAllByText("Vietnamese Demo").length).toBeGreaterThan(0);
    expect(screen.getAllByText("gated").length).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: "Install voice" }),
    ).not.toBeInTheDocument();
  });

  it("supports search, sort, and install polling states", async () => {
    renderWithProviders(<VoicesPanel token="test-token" />);

    await waitFor(() =>
      expect(screen.getAllByText("Vietnamese Demo").length).toBeGreaterThan(0),
    );
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Sort voices" }),
      "engine",
    );
    await userEvent.type(screen.getByLabelText("Search voices"), "French");
    expect(screen.queryAllByText("English Demo")).toHaveLength(0);
    expect(screen.queryAllByText("Vietnamese Demo")).toHaveLength(0);

    // Both desktop table and mobile card render the button — click the first one.
    const installButtons = screen.getAllByRole("button", {
      name: "Install voice",
    });
    await userEvent.click(installButtons[0]);
    expect(screen.getByText("Confirm voice install")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() =>
      expect(screen.getByText("Install succeeded.")).toBeInTheDocument(),
    );
  });

  it("does not load voices without a token", () => {
    renderWithProviders(<VoicesPanel token="" />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Enter a token to load voices.",
    );
    expect(screen.queryAllByText("English Demo")).toHaveLength(0);
  });
});
