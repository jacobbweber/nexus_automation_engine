import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

describe("App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the product title", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, statusText: "x", json: async () => ({}) }),
    );
    render(<App />);
    expect(screen.getByText("Nexus Automation Engine")).toBeInTheDocument();
    // Let the health fetch settle so the state update is wrapped in act().
    await waitFor(() => expect(screen.getByTestId("health-error")).toBeInTheDocument());
  });

  it("shows backend health when reachable", async () => {
    const health = {
      status: "ok",
      app: "Nexus Automation Engine",
      version: "0.1.0",
      environment: "test",
      simulation_mode: true,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => health }),
    );
    render(<App />);
    await waitFor(() => expect(screen.getByTestId("health-ok")).toBeInTheDocument());
    expect(screen.getByTestId("health-ok")).toHaveTextContent("v0.1.0");
  });
});
