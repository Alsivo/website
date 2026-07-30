import { getAllBlogPosts } from "../../lib/blog";
import {
  SITE_DESCRIPTION,
  SITE_NAME,
  SITE_URL,
} from "../../lib/site";

function escapeXml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

export async function GET(): Promise<Response> {
  const posts = getAllBlogPosts();

  const items = posts
    .map((post) => {
      const postUrl = `${SITE_URL}/blog/${post.slug}`;

      return `
        <item>
          <title>${escapeXml(post.title)}</title>
          <link>${postUrl}</link>
          <guid isPermaLink="true">${postUrl}</guid>
          <description>${escapeXml(post.description)}</description>
          <pubDate>${new Date(post.date).toUTCString()}</pubDate>
          <category>${escapeXml(post.category)}</category>
        </item>
      `;
    })
    .join("");

  const rss = `<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>${escapeXml(SITE_NAME)}</title>
    <link>${SITE_URL}</link>
    <description>${escapeXml(SITE_DESCRIPTION)}</description>
    <language>ja</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link
      href="${SITE_URL}/feed.xml"
      rel="self"
      type="application/rss+xml"
      xmlns:atom="http://www.w3.org/2005/Atom"
    />
    ${items}
  </channel>
</rss>`;

  return new Response(rss, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      "Cache-Control":
        "public, s-maxage=3600, stale-while-revalidate=86400",
    },
  });
}