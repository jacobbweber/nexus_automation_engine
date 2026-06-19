// Tiny dependency-free fuzzy matcher for the command palette. Subsequence match with bonuses for
// contiguous runs and start-of-string hits; returns null when the query isn't a subsequence.

export function fuzzyMatch(query: string, text: string): number | null {
  const q = query.toLowerCase().trim();
  const t = text.toLowerCase();
  if (!q) return 0;
  let ti = 0;
  let score = 0;
  for (const ch of q) {
    const idx = t.indexOf(ch, ti);
    if (idx === -1) return null;
    if (idx === ti) score += 2; // contiguous with previous match
    if (idx === 0) score += 3; // start of string
    score += 1;
    ti = idx + 1;
  }
  return score - (t.length - q.length) * 0.01; // mild preference for tighter matches
}

export interface Rankable {
  label: string;
  keywords?: string;
}

export function rank<T extends Rankable>(items: T[], query: string): T[] {
  if (!query.trim()) return items;
  return items
    .map((item) => ({ item, score: fuzzyMatch(query, `${item.label} ${item.keywords ?? ""}`) }))
    .filter((r): r is { item: T; score: number } => r.score !== null)
    .sort((a, b) => b.score - a.score)
    .map((r) => r.item);
}
