import type { Metadata } from "next";
import Link from "next/link";
import { getAllBlogPosts } from "../../lib/blog";

export const metadata: Metadata = {
  title: "AI Blog",
  description:
    "AIツール、生成AI、仕事効率化に関する実践的な情報を発信します。",
};

export default function BlogPage() {
  const articles = getAllBlogPosts();

  return (
    <main className="page-shell blog-page">
      <section className="page-hero">
        <p className="section-kicker">BLOG</p>

        <h1>
          AIを知り、
          <br />
          仕事に活かす。
        </h1>

        <p className="page-description">
          AIツール、生成AI、仕事効率化に関する情報を、
          分かりやすく実践的に紹介します。
        </p>
      </section>

      <section className="article-list-section">
        <div className="article-list-header">
          <h2>Latest Articles</h2>

          <p>
            {articles.length} {articles.length === 1 ? "Article" : "Articles"}
          </p>
        </div>

        {articles.length === 0 ? (
          <p className="empty-message">
            現在公開中の記事はありません。
          </p>
        ) : (
          <div className="article-card-grid">
            {articles.map((article) => {
              const formattedDate = new Intl.DateTimeFormat("ja-JP", {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
              }).format(new Date(article.date));

              return (
                <Link
                  className="article-card"
                  href={`/blog/${article.slug}`}
                  key={article.slug}
                >
                  <div className="article-card-visual">
                    <span>{article.category}</span>
                    <strong>AI</strong>
                  </div>

                  <div className="article-card-body">
                    <div className="article-card-meta">
                      <time dateTime={article.date}>{formattedDate}</time>
                      <span>{article.readingTime}</span>
                    </div>

                    <h2>{article.title}</h2>

                    <p>{article.description}</p>

                    <div className="article-card-tags">
                      {article.tags.slice(0, 3).map((tag: string) => (
                        <span key={tag}>{tag}</span>
                      ))}
                    </div>

                    <span className="article-card-link">
                      記事を読む
                      <span aria-hidden="true">→</span>
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}