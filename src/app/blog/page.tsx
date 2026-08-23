import type { Metadata } from "next";
import BlogExplorer from "../../components/BlogExplorer";
import { getAllBlogPosts } from "../../lib/blog";

export const metadata: Metadata = {
  title: "AI Blog",
  description:
    "AIツール、生成AI、仕事効率化などに関する実践的な情報を発信します。",
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
          生活に活かす。
        </h1>

        <p className="page-description">
          <span className="desktop-copy copy-line">
            AIツール、生成AI、仕事効率化などに関する情報を、分かりやすく実践的に紹介します。
          </span>
          <span className="mobile-copy">
            <span className="copy-line">AIツール、生成AI、仕事効率化などに関する</span>
            <br />
            <span className="copy-line">情報を、分かりやすく実践的に紹介します。</span>
          </span>
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
