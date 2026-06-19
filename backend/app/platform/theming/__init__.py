"""Server-side theming: validated theme storage (volume) + REST + change stream.

The deterministic validator mirrors the frontend `theme-schema.ts` so a theme is only ever served
or saved if it passes the same allow-list + WCAG-AA gate. No AI is involved anywhere (ADR-0008).
"""
