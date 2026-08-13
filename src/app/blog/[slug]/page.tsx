import {
  createArticleJsonLd,
  createBreadcrumbJsonLd,
  createFaqJsonLd,
  serializeJsonLd,
} from "../../../lib/structured-data";
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { extractTableOfContents } from "../../../lib/headings";
import MdxContent from "../../../components/MdxContent";
import {
  extractArticleCta,
  getAllBlogSlugs,
  getBlogPostBySlug,
  getRelatedBlogPosts,
  removeArticleCta,
} from "../../../lib/blog";
import {
  SITE_NAME,
  SITE_URL,
} from "../../../lib/site";
import AffiliateLink from "../../../components/AffiliateLink";

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

  const articleJsonLd =
    createArticleJsonLd(post);

  const breadcrumbJsonLd =
    createBreadcrumbJsonLd(post);

  const faqJsonLd =
    createFaqJsonLd(post);

  const tableOfContents = extractTableOfContents(
    post.content,
  );

  const afterTocCta = extractArticleCta(
    post.content,
    "after_toc",
  );

  const articleContent = removeArticleCta(
    post.content,
    "after_toc",
    "primary",
  );

  const relatedPosts = getRelatedBlogPosts(
    post.slug,
    post.category,
    post.tags,
    3,
  );

  const publishedDate = new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(post.date));

  const verifiedSourceDate =
    post.verified
    ?? post.updated
    ?? post.date;

  const verifiedDate = new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(
    new Date(verifiedSourceDate),
  );

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: serializeJsonLd(
            articleJsonLd,
          ),
        }}
      />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: serializeJsonLd(
            breadcrumbJsonLd,
          ),
        }}
      />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: serializeJsonLd(
            faqJsonLd,
          ),
        }}
      />

      <main>
        <article className="article-page">
        <Link className="article-back-link" href="/blog">
          ← Blogへ戻る
        </Link>

        <p className="article-category">{post.category}</p>

        <h1>{post.title}</h1>

        <p className="article-lead">{post.description}</p>

        <div className="article-meta-row">
          <time dateTime={post.date}>{publishedDate}</time>
          <span>{post.readingTime}</span>
        </div>

        <div className="article-tag-list">
          {post.tags.map((tag: string) => (
            <span key={tag}>{tag}</span>
          ))}
        </div>

        <aside
          className="article-information-note"
          aria-label="記事情報について"
        >
          <p className="article-information-note-title">
            情報について
          </p>

          <p>
            この記事は
            <strong>{verifiedDate}</strong>
            時点の情報に基づいています。
            料金・機能・利用条件などは変更されている可能性があります。
            最新情報は各サービスの公式サイトをご確認ください。
          </p>
        </aside>

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

        {afterTocCta && (
          <div className="article-after-toc-cta">
            <AffiliateLink
              href={afterTocCta.href}
              service={afterTocCta.service}
              linkType={afterTocCta.linkType}
              network={afterTocCta.network}
              ctaType={afterTocCta.ctaType}
              ctaPlacement="after_toc"
            >
              {afterTocCta.label}
            </AffiliateLink>
          </div>
        )}

        <div className="article-content">
          <MdxContent source={articleContent} />
        </div>
        {relatedPosts.length > 0 && (
          <section
            className="related-posts"
            aria-labelledby="related-posts-title"
          >
            <div className="related-posts-header">
              <div>
                <p className="section-kicker">
                  RELATED
                </p>

                <h2 id="related-posts-title">
                  関連記事
                </h2>
              </div>

              <Link href="/blog">
                すべての記事を見る →
              </Link>
            </div>

            <div className="related-posts-grid">
              {relatedPosts.map((relatedPost) => {
                const formattedDate =
                  new Intl.DateTimeFormat("ja-JP", {
                    year: "numeric",
                    month: "2-digit",
                    day: "2-digit",
                  }).format(
                    new Date(relatedPost.date),
                  );

                return (
                  <Link
                    className="related-post-card"
                    href={`/blog/${relatedPost.slug}`}
                    key={relatedPost.slug}
                  >
                    <div className="related-post-image">
                      <Image
                        src={relatedPost.image}
                        alt={`${relatedPost.title}のアイキャッチ画像`}
                        fill
                        sizes="(max-width: 700px) 100vw, 33vw"
                      />
                    </div>

                    <div className="related-post-body">
                      <div className="related-post-meta">
                        <span>
                          {relatedPost.category}
                        </span>

                        <time dateTime={relatedPost.date}>
                          {formattedDate}
                        </time>
                      </div>

                      <h3>{relatedPost.title}</h3>

                      <p>{relatedPost.description}</p>

                      <span className="related-post-link">
                        記事を読む →
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </section>
        )}
        </article>
      </main>
    </>
  );
}