// The 10 built-in themes (B11). Each is built from the validated base + small overrides and is
// run through validateTheme() in builtins.test.ts (the real AA gate). Status colors mostly inherit
// the base so run statuses stay distinguishable and AA across themes.

import type { ThemeDoc } from "../theme-schema";
import { buildTheme } from "./base";

export type BuiltinTheme = ThemeDoc & { blurb: string };

export const BUILTIN_THEMES: BuiltinTheme[] = [
  buildTheme({ id: "signal", name: "Signal", base: "light", blurb: "Calm warm-neutral default." }),

  buildTheme(
    { id: "paper", name: "Paper", base: "light", blurb: "Minimalist, high-legibility, sepia." },
    {
      "--bg": "#f7f4ee", "--surface": "#fffdf9", "--surface-2": "#efe9df", "--surface-3": "#e6dfd2",
      "--text": "#1c1a17", "--text-muted": "#665b4e", "--border": "#e2dacb", "--border-strong": "#cabfa9",
      "--accent": "#7a5f2e", "--accent-hover": "#67501f", "--accent-active": "#523f17",
      "--focus": "#7a5f2e", "--link": "#67501f",
    },
    {
      "--accent": "#d8b878", "--accent-hover": "#e3c894", "--accent-active": "#e3c894",
      "--focus": "#d8b878", "--link": "#e3c894",
    },
  ),

  buildTheme(
    { id: "midnight-ops", name: "Midnight Ops", base: "dark", blurb: "Low-glare dark for long NOC sessions." },
    {},
    {
      "--bg": "#0e0d14", "--surface": "#16161f", "--surface-2": "#1d1d28", "--surface-3": "#262633",
      "--text": "#e9eaf2", "--text-muted": "#aab0c2", "--border": "#2a2a38", "--border-strong": "#3a3a4c",
      "--divider": "#1d1d28", "--accent": "#6fb0e6", "--accent-hover": "#97c8ef", "--accent-active": "#97c8ef",
      "--focus": "#6fb0e6", "--link": "#97c8ef",
    },
  ),

  buildTheme(
    { id: "slate-pro", name: "Slate Pro", base: "dark", blurb: "Dense, cool, enterprise." },
    {
      "--bg": "#f2f4f7", "--surface": "#ffffff", "--surface-2": "#e8ebf0", "--surface-3": "#dde2e9",
      "--text": "#161a20", "--text-muted": "#566273", "--border": "#d4d9e1", "--border-strong": "#b9c0cb",
      "--accent": "#2f6aa8", "--accent-hover": "#285a90", "--accent-active": "#214b78",
      "--focus": "#2f6aa8", "--link": "#285a90",
    },
    {
      "--bg": "#0f141b", "--surface": "#161c25", "--surface-2": "#1d2530", "--surface-3": "#28323f",
      "--text": "#e7ecf3", "--text-muted": "#9aa6b8", "--border": "#28323f", "--border-strong": "#3a4757",
      "--divider": "#1d2530", "--accent": "#5aa0e0", "--accent-hover": "#86bcee", "--accent-active": "#86bcee",
      "--focus": "#5aa0e0", "--link": "#86bcee",
    },
  ),

  buildTheme(
    { id: "focus-flow", name: "Focus Flow", base: "light", blurb: "ADHD spotlight — muted field, one focal accent." },
    {
      "--bg": "#f4f3f1", "--surface": "#faf9f7", "--surface-2": "#eceae6", "--surface-3": "#e2e0da",
      "--text": "#1d1c1a", "--text-muted": "#64625d", "--border": "#e0ded9", "--border-strong": "#c7c4bd",
      "--accent": "#0d7a6f", "--accent-hover": "#0a655c", "--accent-active": "#084f48",
      "--focus": "#0d7a6f", "--link": "#0a655c",
    },
    {
      "--bg": "#15151a", "--surface": "#1c1c22", "--surface-2": "#24242c", "--surface-3": "#2d2d36",
      "--text": "#ecebf0", "--text-muted": "#a6a4ad", "--border": "#2a2a32", "--border-strong": "#3a3a44",
      "--accent": "#2fd0bd", "--accent-hover": "#54dccb", "--accent-active": "#54dccb",
      "--focus": "#2fd0bd", "--link": "#54dccb",
    },
  ),

  buildTheme(
    { id: "calm-clarity", name: "Calm Clarity", base: "light", blurb: "ADHD low-arousal — muted, motion-minimal." },
    {
      "--bg": "#eef0ec", "--surface": "#f6f7f4", "--surface-2": "#e6e9e2", "--surface-3": "#dde1d8",
      "--text": "#252822", "--text-muted": "#5c6056", "--border": "#d7dbcf", "--border-strong": "#bcc1b2",
      "--accent": "#3f7d74", "--accent-hover": "#356a62", "--accent-active": "#2b554f",
      "--focus": "#3f7d74", "--link": "#356a62",
    },
    {
      "--bg": "#1a1c19", "--surface": "#21241f", "--surface-2": "#292c26", "--surface-3": "#333730",
      "--text": "#e8eae4", "--text-muted": "#a4a89c", "--border": "#2f322b", "--border-strong": "#3f433a",
      "--accent": "#7cc3b6", "--accent-hover": "#9bd2c8", "--accent-active": "#9bd2c8",
      "--focus": "#7cc3b6", "--link": "#9bd2c8",
    },
  ),

  buildTheme(
    { id: "high-contrast", name: "High Contrast", base: "light", blurb: "Maximum accessibility (AAA)." },
    {
      "--bg": "#ffffff", "--surface": "#ffffff", "--surface-2": "#f2f2f2", "--surface-3": "#e6e6e6",
      "--text": "#000000", "--text-muted": "#1a1a1a", "--text-subtle": "#333333",
      "--border": "#000000", "--border-strong": "#000000", "--divider": "#000000",
      "--accent": "#0033aa", "--accent-hover": "#002b8e", "--accent-active": "#00237a", "--accent-contrast": "#ffffff",
      "--success": "#006400", "--warn": "#8a5a00", "--danger": "#b00000", "--info": "#00457a",
      "--run-running": "#0033aa", "--run-ok": "#006400", "--run-warn": "#8a5a00",
      "--run-failed": "#b00000", "--run-skipped": "#444444", "--focus": "#0033aa", "--link": "#0033aa",
    },
    {
      "--bg": "#000000", "--surface": "#000000", "--surface-2": "#111111", "--surface-3": "#1c1c1c",
      "--text": "#ffffff", "--text-muted": "#e6e6e6", "--text-subtle": "#cccccc",
      "--border": "#ffffff", "--border-strong": "#ffffff", "--divider": "#ffffff",
      "--accent": "#66aaff", "--accent-hover": "#8cc0ff", "--accent-active": "#8cc0ff", "--accent-contrast": "#000000",
      "--success": "#5ad15a", "--warn": "#e8b84b", "--danger": "#ff6b6b", "--info": "#5ab0e8",
      "--run-running": "#66aaff", "--run-ok": "#5ad15a", "--run-warn": "#e8b84b",
      "--run-failed": "#ff6b6b", "--run-skipped": "#bbbbbb", "--focus": "#66aaff", "--link": "#66aaff",
    },
  ),

  buildTheme(
    { id: "terminal", name: "Terminal", base: "dark", blurb: "Retro green-on-black (AA-tuned)." },
    {
      "--accent": "#1f7a1f", "--accent-hover": "#1a661a", "--accent-active": "#145014",
      "--focus": "#1f7a1f", "--link": "#1a661a",
    },
    {
      "--bg": "#0a0e0a", "--surface": "#0f140f", "--surface-2": "#141a14", "--surface-3": "#1c241c",
      "--text": "#d7f5d7", "--text-muted": "#8cc08c", "--border": "#1f2a1f", "--border-strong": "#2c3c2c",
      "--divider": "#141a14", "--accent": "#46d246", "--accent-hover": "#6fe06f", "--accent-active": "#6fe06f",
      "--accent-contrast": "#0a0e0a", "--run-running": "#46d246", "--run-ok": "#6fe06f", "--run-warn": "#e0b84a",
      "--run-failed": "#ff6f5e", "--run-skipped": "#7a8a7a", "--focus": "#46d246", "--link": "#6fe06f",
      "--success": "#46d246", "--warn": "#e0b84a", "--danger": "#ff6f5e", "--info": "#5ad0c0",
    },
  ),

  buildTheme(
    { id: "daylight", name: "Daylight", base: "light", blurb: "Bright, high-clarity for war rooms & projectors." },
    {
      "--bg": "#ffffff", "--surface": "#ffffff", "--surface-2": "#eef1f5", "--surface-3": "#e2e7ee",
      "--text": "#0d1117", "--text-muted": "#44505f", "--border": "#c9d2dd", "--border-strong": "#a7b3c1",
      "--accent": "#0b5fb0", "--accent-hover": "#094f93", "--accent-active": "#073f76",
      "--success": "#1f7a43", "--warn": "#8a5a10", "--danger": "#b3261e", "--info": "#0b5f86",
      "--run-running": "#0b5fb0", "--run-ok": "#1f7a43", "--run-warn": "#8a5a10",
      "--run-failed": "#b3261e", "--run-skipped": "#566573", "--focus": "#0b5fb0", "--link": "#094f93",
    },
    {
      "--accent": "#5aa6f0", "--accent-hover": "#86c0f5", "--accent-active": "#86c0f5",
      "--focus": "#5aa6f0", "--link": "#86c0f5",
    },
  ),

  buildTheme(
    { id: "ember", name: "Ember", base: "dark", blurb: "Warm, low-blue for long incident bridges." },
    {
      "--bg": "#faf3ec", "--surface": "#fffaf4", "--surface-2": "#f1e7db", "--surface-3": "#e8d9c8",
      "--text": "#2a201a", "--text-muted": "#6e5d4e", "--border": "#e7d8c6", "--border-strong": "#cdb89f",
      "--accent": "#b05a86", "--accent-hover": "#964a72", "--accent-active": "#7c3c5e",
      "--focus": "#b05a86", "--link": "#964a72",
    },
    {
      "--bg": "#1a1512", "--surface": "#221b16", "--surface-2": "#2a211b", "--surface-3": "#352a22",
      "--text": "#f3e9df", "--text-muted": "#c2ad99", "--border": "#3a2d23", "--border-strong": "#4d3c2f",
      "--divider": "#2a211b", "--accent": "#e08fb0", "--accent-hover": "#e8a8c2", "--accent-active": "#e8a8c2",
      "--accent-contrast": "#1a1512", "--focus": "#e08fb0", "--link": "#e8a8c2",
    },
  ),
];

export const DEFAULT_THEME_ID = "signal";
