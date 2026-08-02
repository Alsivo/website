import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { extractTableOfContents } from "../../../lib/headings";
import MdxContent from "../../../components/MdxContent";
import {
  getAllBlogSlugs,
  getBlogPostBySlug,
} from "../../../lib/blog";
import {
  SITE_NAME,
  SITE_URL,
} from "../../../lib/site";

type BlogPostPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export function generateStaticParams() {
  return getAllBlogSlugs().map((slug) => ({
    slug,
  }));
}

export async function generateMetadata({
  params,
}: BlogPostPageProps): Promise<Metadata> {
  const { slug } = await params;
  const post = getBlogPostBySlug(slug);

  if (!post) {
    return {
      title: "記事が見つかりません",
      robots: {
        index: false,
        follow: false,
      },
    };
  }

  const articleUrl = `${SITE_URL}/blog/${post.slug}`;

  return {
    title: `${post.title} | ${SITE_NAME}`,
    description: post.description,

    alternates: {
      canonical: articleUrl,
    },

    openGraph: {
      type: "article",
      locale: "ja_JP",
      siteName: SITE_NAME,
      title: post.title,
      description: post.description,
      url: articleUrl,
      publishedTime: post.date,
      modifiedTime: post.updated ?? post.date,
      tags: post.tags,
    },

    twitter: {
      card: "summary_large_image",
      title: post.title,
      description: post.description,
    },
  };
}

export default async function BlogPostPage({
  params,
}: BlogPostPageProps) {
  const { slug } = await params;
  const post = getBlogPostBySlug(slug);

  if (!post) {
    notFound();
  }

  const tableOfContents = extractTableOfContents(
    post.content,
  );

  const articleUrl = `${SITE_URL}/blog/${post.slug}`;

  const publishedDate = new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(post.date));

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: post.title,
    description: post.description,
    datePublished: post.date,
    dateModified: post.updated ?? post.date,
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": articleUrl,
    },
    author: {
      "@type": "Organization",
      name: SITE_NAME,
      url: SITE_URL,
    },
    publisher: {
      "@type": "Organization",
      name: SITE_NAME,
      url: SITE_URL,
    },
    keywords: post.tags.join(", "),
    articleSection: post.category,
    inLanguage: "ja-JP",
  };

  return (
    <main>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />

      <article className="article-page">
        <Link className="article-back-link" href="/blog">
          ← Blogへ戻る
        </Link>

        <p className="article-category">{post.category}</p>

        <h1>{post.title}</h1>

        <p className="article-lead">{post.description}</p>

        <div className="article-hero-image">
          <Image
            src={post.image}
            alt={`${post.title}のアイキャッチ画像`}
            fill
            priority
            sizes="(max-width: 820px) 100vw, 780px"
          />
        </div>

        <div className="article-meta-row">
          <time dateTime={post.date}>{publishedDate}</time>
          <span>{post.readingTime}</span>
        </div>

        <div className="article-tag-list">
          {post.tags.map((tag: string) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>

        {tableOfContents.length > 0 && (
          <nav
            className="article-toc"
            aria-label="記事の目次"
          >
            <p className="article-toc-title">
              目次
            </p>

            <ol>
              {tableOfContents.map((item) => (
                <li
                  className={
                    item.level === 3
                      ? "article-toc-level-3"
                      : undefined
                  }
                  key={`${item.level}-${item.id}`}
                >
                  <a href={`#${item.id}`}>
                    {item.text}
                  </a>
                </li>
              ))}
            </ol>
          </nav>
        )}

        <div className="article-content">
          <MdxContent source={post.content} />
        </div>
      </article>
    </main>
  );
}