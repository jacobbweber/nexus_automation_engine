import { describe, expect, it } from "vitest";
import { resolveMode, type ModeState } from "./mode-core";

const base: ModeState = {
  preference: "system",
  sundown: { enabled: false, start: "18:00", end: "06:00" },
  perArea: {},
};
const at = (h: number) => new Date(2026, 0, 1, h, 0, 0);

describe("resolveMode", () => {
  it("honors explicit light/dark preference", () => {
    expect(resolveMode({ ...base, preference: "light" }, { osDark: true, now: at(12) })).toBe("light");
    expect(resolveMode({ ...base, preference: "dark" }, { osDark: false, now: at(12) })).toBe("dark");
  });

  it("system follows the OS when sundown is off", () => {
    expect(resolveMode(base, { osDark: true, now: at(12) })).toBe("dark");
    expect(resolveMode(base, { osDark: false, now: at(12) })).toBe("light");
  });

  it("system + sundown goes dark within an overnight window", () => {
    const s = { ...base, sundown: { enabled: true, start: "18:00", end: "06:00" } };
    expect(resolveMode(s, { osDark: false, now: at(20) })).toBe("dark"); // evening
    expect(resolveMode(s, { osDark: true, now: at(3) })).toBe("dark"); // small hours
    expect(resolveMode(s, { osDark: true, now: at(12) })).toBe("light"); // midday
  });

  it("a per-area override beats the global preference", () => {
    const s = { ...base, preference: "light" as const, perArea: { console: "dark" as const } };
    expect(resolveMode(s, { osDark: false, now: at(12), activeArea: "console" })).toBe("dark");
    expect(resolveMode(s, { osDark: false, now: at(12), activeArea: "catalog" })).toBe("light");
  });
});
