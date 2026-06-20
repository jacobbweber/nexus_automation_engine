// Regression (QA): the mode engine must keep the legacy `.dark` class (set in index.html for
// anti-FOUC) in sync with the resolved mode. A stale `.dark` pins `:where(.dark)` to dark tokens
// even after the user picks Light.

import { act } from "react";
import { render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { ModeProvider, useMode } from "./mode";

function matchMediaStub(matches: boolean) {
  return (query: string) => ({
    matches: query.includes("dark") ? matches : false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  });
}

let setPref: (p: "system" | "light" | "dark") => void;

function Probe() {
  const mode = useMode();
  setPref = mode.setPreference;
  return null;
}

describe("ModeProvider keeps .dark in sync", () => {
  beforeEach(() => {
    localStorage.clear();
    // Start as index.html does (anti-FOUC) and pretend the OS prefers dark.
    document.documentElement.className = "dark";
    window.matchMedia = matchMediaStub(true) as unknown as typeof window.matchMedia;
  });
  afterEach(() => {
    document.documentElement.className = "";
    document.documentElement.removeAttribute("data-mode");
  });

  it("removes .dark when the user switches to light, restores it on dark", () => {
    render(
      <ModeProvider>
        <Probe />
      </ModeProvider>,
    );
    const root = document.documentElement;

    act(() => setPref("light"));
    expect(root.dataset.mode).toBe("light");
    expect(root.classList.contains("dark")).toBe(false);

    act(() => setPref("dark"));
    expect(root.dataset.mode).toBe("dark");
    expect(root.classList.contains("dark")).toBe(true);
  });
});
