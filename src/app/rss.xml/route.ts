import { getAllBlogPosts } from "../../lib/blog";
import {
  SITE_NAME,
  SITE_URL,
} from "../../lib/site";

export const dynamic = "force-static";

function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export async function GET() {
  const posts = getAllBlogPosts();

  const items = posts
    .map((post) => {
      const articleUrl =
        `${SITE_URL}/blog/${post.slug}`;

      const publishedDate = new Date(
        post.date,
      ).toUTCString();

      return `
    <item>
      <title>${escapeXml(post.title)}</title>
      <link>${escapeXml(articleUrl)}</link>
      <guid isPermaLink="true">${escapeXml(articleUrl)}</guid>
      <pubDate>${publishedDate}</pubDate>
      <description>${escapeXml(post.description)}</description>
      <category>${escapeXml(post.category)}</category>
    </item>`;
    })
    .join("");

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss
  version="2.0"
  xmlns:atom="http://www.w3.org/2005/Atom"
>
  <channel>
    <title>${escapeXml(SITE_NAME)}</title>
    <link>${escapeXml(SITE_URL)}</link>
    <description>${escapeXml(
      "AIツール、生成AI、仕事効率化に関する実践情報を発信するAlsivoのRSSフィードです。",
    )}</description>
    <language>ja</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link
      href="${escapeXml(`${SITE_URL}/rss.xml`)}"
      rel="self"
      type="application/rss+xml"
    />
    ${items}
  </channel>
</rss>`;

  return new Response(
    rss,
    {
      headers: {
        "Content-Type":
          "application/rss+xml; charset=utf-8",
        "Cache-Control":
          "public, max-age=0, s-maxage=3600",
      },
    },
  );
}