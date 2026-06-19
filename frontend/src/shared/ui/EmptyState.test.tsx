import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmptyState } from "./EmptyState";

describe("EmptyState", () => {
  it("renders title, description, and an action", () => {
    render(
      <EmptyState
        title="No workflows yet"
        description="They will show up here."
        action={<button>Create one</button>}
      />,
    );
    expect(screen.getByText("No workflows yet")).toBeTruthy();
    expect(screen.getByText("They will show up here.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Create one" })).toBeTruthy();
  });

  it("renders a default icon and is announced to screen readers", () => {
    const { container } = render(<EmptyState title="Nothing here" />);
    expect(container.querySelector("svg")).toBeTruthy();
    expect(screen.getByRole("status")).toBeTruthy();
  });
});
