import type { Metadata } from "next";
import BlogExplorer from "../../components/BlogExplorer";
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
        {articles.length === 0 ? (
          <p className="empty-message">
            現在公開中の記事はありません。
          </p>
        ) : (
          <BlogExplorer articles={articles} />
        )}
      </section>
    </main>
  );
}