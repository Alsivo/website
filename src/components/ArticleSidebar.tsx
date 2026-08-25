import Image from "next/image";
import Link from "next/link";
import type { BlogPostSummary } from "@/types/blog";

function SidebarList({
  articles,
}: {
  articles: BlogPostSummary[];
}) {
  return (
    <ol className="article-sidebar-list">
      {articles.map((article, index) => (
        <li key={article.slug}>
          <Link href={`/blog/${article.slug}`}>
            <span className="article-sidebar-rank">{String(index + 1).padStart(2, "0")}</span>
            <span className="article-sidebar-image">
              <Image src={article.image} alt="" fill sizes="88px" quality={100} />
            </span>
            <span className="article-sidebar-copy">
              <strong>{article.title}</strong>
              <time dateTime={article.date}>{article.date.replaceAll("-", ".")}</time>
            </span>
          </Link>
        </li>
      ))}
    </ol>
  );
}

export default function ArticleSidebar({
  popular,
  latest,
}: {
  popular: BlogPostSummary[];
  latest: BlogPostSummary[];
}) {
  if (popular.length === 0 && latest.length === 0) return null;

  return (
    <aside className="article-sidebar" aria-label="人気記事と最新記事">
      <section>
        <p className="section-kicker">POPULAR</p>
        <h2>人気記事 Top 5</h2>
        <SidebarList articles={popular.slice(0, 5)} />
      </section>
      <section>
        <p className="section-kicker">LATEST</p>
        <h2>最新記事</h2>
        <SidebarList articles={latest.slice(0, 5)} />
      </section>
    </aside>
  );
}
