export type TableOfContentsItem = {
  id: string;
  text: string;
  level: 2 | 3;
};

export function createHeadingId(text: string): string {
  const normalized = text
    .trim()
    .toLowerCase()
    .replace(/[。、，．・：；！？!?,.:;'"“”‘’（）()【】[\]{}]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");

  return normalized || "section";
}

export function extractTableOfContents(
  markdown: string,
): TableOfContentsItem[] {
  const headingPattern = /^(##|###)\s+(.+)$/gm;
  const items: TableOfContentsItem[] = [];
  const usedIds = new Map<string, number>();

  let match: RegExpExecArray | null;

  while ((match = headingPattern.exec(markdown)) !== null) {
    const level = match[1].length as 2 | 3;
    const text = match[2]
      .replace(/\[(.*?)\]\(.*?\)/g, "$1")
      .replace(/[*_`]/g, "")
      .trim();

    const baseId = createHeadingId(text);
    const currentCount = usedIds.get(baseId) ?? 0;
    const id =
      currentCount === 0
        ? baseId
        : `${baseId}-${currentCount + 1}`;

    usedIds.set(baseId, currentCount + 1);

    items.push({
      id,
      text,
      level,
    });
  }

  return items;
}