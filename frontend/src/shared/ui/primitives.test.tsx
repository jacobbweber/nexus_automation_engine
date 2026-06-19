import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Button, StatusBadge } from "./primitives";

describe("StatusBadge (protected status)", () => {
  it("renders a label + an icon (shape, not color-only) for a run status", () => {
    const { container } = render(<StatusBadge status="failed" />);
    expect(screen.getByText("failed")).toBeTruthy();
    // an svg icon accompanies the label so status is never conveyed by color alone
    expect(container.querySelector("svg")).toBeTruthy();
  });

  it("humanizes underscored lifecycle states", () => {
    render(<StatusBadge status="changes_requested" />);
    expect(screen.getByText("changes requested")).toBeTruthy();
  });

  it("falls back gracefully for an unknown status", () => {
    const { container } = render(<StatusBadge status="weird_state" />);
    expect(screen.getByText("weird state")).toBeTruthy();
    expect(container.querySelector("svg")).toBeTruthy();
  });
});

describe("Button", () => {
  it("fires onClick and respects disabled", () => {
    const onClick = vi.fn();
    const { rerender } = render(<Button onClick={onClick}>Run</Button>);
    screen.getByText("Run").click();
    expect(onClick).toHaveBeenCalledTimes(1);
    rerender(
      <Button onClick={onClick} disabled>
        Run
      </Button>,
    );
    screen.getByText("Run").click();
    expect(onClick).toHaveBeenCalledTimes(1); // disabled = no second call
  });
});
