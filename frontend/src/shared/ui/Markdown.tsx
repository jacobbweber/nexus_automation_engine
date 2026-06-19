// Minimal, dependency-free Markdown renderer for automation docs.
// Supports: # / ## / ### headings, - bullet lists, **bold**, `code`, and paragraphs.

function inline(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, '<code style="background:var(--surface-2);padding:1px 5px;border-radius:4px">$1</code>');
}

export function Markdown({ source }: { source: string }) {
  const lines = source.split("\n");
  const blocks: string[] = [];
  let list: string[] = [];

  const flush = () => {
    if (list.length) {
      blocks.push(`<ul style="margin:6px 0 6px 18px">${list.map((i) => `<li>${inline(i)}</li>`).join("")}</ul>`);
      list = [];
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (line.startsWith("### ")) {
      flush();
      blocks.push(`<h4 style="margin:12px 0 4px">${inline(line.slice(4))}</h4>`);
    } else if (line.startsWith("## ")) {
      flush();
      blocks.push(`<h3 style="margin:14px 0 6px">${inline(line.slice(3))}</h3>`);
    } else if (line.startsWith("# ")) {
      flush();
      blocks.push(`<h2 style="margin:8px 0 8px;font-size:1.15rem">${inline(line.slice(2))}</h2>`);
    } else if (line.startsWith("- ")) {
      list.push(line.slice(2));
    } else if (line.trim() === "") {
      flush();
    } else {
      flush();
      blocks.push(`<p style="margin:6px 0;line-height:1.5">${inline(line)}</p>`);
    }
  }
  flush();

  return (
    <div
      style={{ fontSize: "0.9rem", color: "var(--text)" }}
      dangerouslySetInnerHTML={{ __html: blocks.join("") }}
    />
  );
}
