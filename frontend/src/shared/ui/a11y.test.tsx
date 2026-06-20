// Automated structural accessibility checks (L47): assert key shared components expose correct
// roles + accessible names. Color contrast is gated separately by contrast.test.ts (A7); a full
// browser/screen-reader audit is the remaining manual step.

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button, StatusBadge } from "./primitives";
import { EmptyState } from "./EmptyState";
import { ConnectionBanner } from "./ConnectionBanner";

describe("component accessibility (structural)", () => {
  it("Button exposes an accessible name", () => {
    render(<Button>Run workflow</Button>);
    expect(screen.getByRole("button", { name: "Run workflow" })).toBeTruthy();
  });

  it("StatusBadge conveys status as text (not color alone)", () => {
    render(<StatusBadge status="failed" />);
    expect(screen.getByText("failed")).toBeTruthy();
  });

  it("EmptyState is a status region with a heading + action", () => {
    render(<EmptyState title="Nothing here" action={<button>Create</button>} />);
    expect(screen.getByRole("status")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Create" })).toBeTruthy();
  });

  it("ConnectionBanner renders nothing while healthy (non-blocking by default)", () => {
    const { container } = render(<ConnectionBanner />);
    expect(container.firstChild).toBeNull();
  });
});
