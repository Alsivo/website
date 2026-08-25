import type { Metadata } from "next";
import BlogExplorer from "../../components/BlogExplorer";
import Image from "next/image";
import { getAllBlogPosts } from "../../lib/blog";
import ArticleSidebar from "../../components/ArticleSidebar";

export const metadata: Metadata = {
  title: "AI Blog",
  description:
    "AIツール、生成AI、仕事効率化などに関する実践的な情報を発信します。",
};

export default function BlogPage() {
  const articles = getAllBlogPosts();

  return (
    <main className="page-shell blog-page">
      <section className="page-hero page-hero-with-characters">
        <div className="page-hero-copy">
        <p className="section-kicker">BLOG</p>

        <h1>
          AIを知り、
          <br />
          生活に活かす。
        </h1>

        <p className="page-description">日々の悩みを解決するAIツールや生成AIについて<br />アルとシーボが実例を通じて解説します。</p>
        </div>
        <div className="blog-hero-characters">
          <div className="blog-hero-character blog-hero-al"><span>実際によくある悩みをもとに</span><div><Image src="/images/characters/al-upper-body-v1.png" alt="アル" fill sizes="180px" quality={100} /></div></div>
          <div className="blog-hero-character blog-hero-cibo"><span>解決策を紹介するね</span><div><Image src="/images/characters/cibo-upper-body-v1.png" alt="シーボ" fill sizes="180px" quality={100} /></div></div>
        </div>
      </section>

      <div className="content-with-sidebar blog-content-with-sidebar">
      <section className="article-list-section">
        {articles.length === 0 ? (
          <p className="empty-message">
            現在公開中の記事はありません。
          </p>
        ) : (
          <BlogExplorer articles={articles} />
        )}
      </section>
      <ArticleSidebar popular={articles.slice(0, 5)} latest={articles.slice(0, 5)} />
      </div>
    </main>
  );
}
