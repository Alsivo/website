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
import ArticleTitle from "../../../components/ArticleTitle";

type BlogPostPageProps = {
  params: Promise<{
    slug: string;
  }>;
};


/* ==========================================================
   Article introduction
   ========================================================== */

function splitArticleH2Sections(
  content: string,
): string[] {
  const normalized = content.trim();

  if (!normalized) {
    return [];
  }

  const starts = Array.from(
    normalized.matchAll(/^##\s+/gm),
  )
    .map((match) => match.index)
    .filter(
      (index): index is number =>
        index !== undefined,
    );

  if (starts.length === 0) {
    return [normalized];
  }

  return starts.map((start, index) =>
    normalized
      .slice(
        start,
        starts[index + 1]
          ?? normalized.length,
      )
      .trim(),
  );
}


export function generateStaticParams() {
  return getAllBlogSlugs().map((slug) => ({
    slug,
  }));
}


export async function generateMetadata({
  params,
}: BlogPostPageProps): Promise<Metadata> {
  const { slug } = await params;

  const post = getBlogPostBySlug(
    slug,
  );

  if (!post) {
    return {
      title: "記事が見つかりません",
      robots: {
        index: false,
        follow: false,
      },
    };
  }

  const articleUrl =
    `${SITE_URL}/blog/${post.slug}`;

  return {
    title:
      `${post.title} | ${SITE_NAME}`,

    description:
      post.description,

    alternates: {
      canonical:
        articleUrl,
    },

    openGraph: {
      type: "article",
      locale: "ja_JP",
      siteName: SITE_NAME,
      title: post.title,
      description:
        post.description,
      url: articleUrl,
      publishedTime:
        post.date,
      modifiedTime:
        post.updated
        ?? post.date,
      tags:
        post.tags,
    },

    twitter: {
      card:
        "summary_large_image",
      title:
        post.title,
      description:
        post.description,
    },
  };
}


export default async function BlogPostPage({
  params,
}: BlogPostPageProps) {
  const { slug } = await params;

  const post = getBlogPostBySlug(
    slug,
  );

  if (!post) {
    notFound();
  }


  /* ========================================================
     Structured data
     ======================================================== */

  const articleJsonLd =
    createArticleJsonLd(
      post,
    );

  const breadcrumbJsonLd =
    createBreadcrumbJsonLd(
      post,
    );

  const faqJsonLd =
    createFaqJsonLd(
      post,
    );


  /* ========================================================
     Table of contents
     ======================================================== */

  const tableOfContents =
    extractTableOfContents(
      post.content,
    );


  /* ========================================================
     CTA
     ======================================================== */

  const afterTocCta =
    extractArticleCta(
      post.content,
      "after_toc",
    );

  const articleContent =
    removeArticleCta(
      removeArticleCta(
        removeArticleCta(
          post.content,
          "after_toc",
        ),
        "after_comparison",
      ),
      "before_faq",
    );

  const isAffiliateArticle =
    /<AffiliateLink\b[\s\S]*?\blinkType=["']affiliate["'][\s\S]*?>/.test(
      post.content,
    );


  /* ========================================================
     Introduction / body separation
     ======================================================== */

  const articleBody = articleContent.trim();

  const articleH2Sections =
    splitArticleH2Sections(
      articleBody,
    );


  /* ========================================================
     Related articles
     ======================================================== */

  const relatedPosts =
    getRelatedBlogPosts(
      post.slug,
      post.category,
      post.tags,
      3,
    );


  /* ========================================================
     Dates
     ======================================================== */

  const publishedDate =
    new Intl.DateTimeFormat(
      "ja-JP",
      {
        year: "numeric",
        month: "long",
        day: "numeric",
      },
    ).format(
      new Date(
        post.date,
      ),
    );

  /* ========================================================
     Render
     ======================================================== */

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html:
            serializeJsonLd(
              articleJsonLd,
            ),
        }}
      />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html:
            serializeJsonLd(
              breadcrumbJsonLd,
            ),
        }}
      />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html:
            serializeJsonLd(
              faqJsonLd,
            ),
        }}
      />

      <main>
        <article className="article-page">

          {/* ===============================================
              Header
              =============================================== */}

          <Link
            className="article-back-link"
            href="/blog"
          >
            ← Blogへ戻る
          </Link>

          {isAffiliateArticle && (
            <p className="article-pr-disclosure">
              PR｜本記事にはアフィリエイト広告が含まれます。
            </p>
          )}

          <p className="article-category">
            {post.category}
          </p>

          <h1>
            <ArticleTitle
              title={post.title}
              lines={post.titleLines}
            />
          </h1>

          <p className="article-lead">
            {post.description}
          </p>

          <div className="article-meta-row">
            <time dateTime={post.date}>
              {publishedDate}
            </time>

            <span>
              {post.readingTime}
            </span>
          </div>

          <div className="article-tag-list">
            {post.tags.map(
              (
                tag: string,
              ) => (
                <span key={tag}>
                  {tag}
                </span>
              ),
            )}
          </div>


          {/* ===============================================
              Hero image
              =============================================== */}

          <div className="article-hero-image">
            <Image
              src={post.image}
              alt={
                `${post.title}のアイキャッチ画像`
              }
              fill
              priority
              sizes="(max-width: 800px) 100vw, 760px"
            />
          </div>


          {/* ===============================================
              Article opening
              =============================================== */}

          <aside className="article-story-promise" aria-label="この記事の相談内容">
            <p><strong>アルの悩み</strong>{post.alQuestion ?? post.description}</p>
            <p><strong>この記事でわかること</strong>{post.ciboAnswer ?? "シーボが悩みをやさしく整理し、次の一歩を紹介します。"}</p>
          </aside>


          {/* ===============================================
              Table of contents
              =============================================== */}

          {tableOfContents.length > 0 && (
            <nav
              className="article-toc"
              aria-label="記事の目次"
            >
              <p className="article-toc-title">
                目次
              </p>

              <ol>
                {tableOfContents.map(
                  (item) => (
                    <li
                      className={
                        item.level === 3
                          ? "article-toc-level-3"
                          : undefined
                      }
                      key={
                        `${item.level}-${item.id}`
                      }
                    >
                      <a
                        href={
                          `#${item.id}`
                        }
                      >
                        {item.text}
                      </a>
                    </li>
                  ),
                )}
              </ol>
            </nav>
          )}


          {/* ===============================================
              Primary CTA
              =============================================== */}

          {afterTocCta && (
            <div className="article-after-toc-cta">
              <AffiliateLink
                href={
                  afterTocCta.href
                }
                service={
                  afterTocCta.service
                }
                linkType={
                  afterTocCta.linkType
                }
                network={
                  afterTocCta.network
                }
                ctaType={
                  afterTocCta.ctaType
                }
                ctaPlacement="after_toc"
                bannerSrc={
                  afterTocCta.bannerSrc
                }
                bannerWidth={
                  afterTocCta.bannerWidth
                }
                bannerHeight={
                  afterTocCta.bannerHeight
                }
                trackingPixelSrc={
                  afterTocCta.trackingPixelSrc
                }
              >
                {afterTocCta.label}
              </AffiliateLink>
            </div>
          )}


          {/* ===============================================
              Article body
              =============================================== */}

          <div className="article-content">
            {isAffiliateArticle
              && afterTocCta
              ? articleH2Sections.map(
                  (section, index) => (
                    <div
                      className="article-cta-section"
                      key={`article-section-${index}`}
                    >
                      <MdxContent
                        source={section}
                      />

                      <div className="article-after-toc-cta">
                        <AffiliateLink
                          href={afterTocCta.href}
                          service={afterTocCta.service}
                          linkType={afterTocCta.linkType}
                          network={afterTocCta.network}
                          ctaType={afterTocCta.ctaType}
                          ctaPlacement="after_section"
                          bannerSrc={afterTocCta.bannerSrc}
                          bannerWidth={afterTocCta.bannerWidth}
                          bannerHeight={afterTocCta.bannerHeight}
                          trackingPixelSrc={afterTocCta.trackingPixelSrc}
                        >
                          {afterTocCta.label}
                        </AffiliateLink>
                      </div>
                    </div>
                  ),
                )
              : (
                  <MdxContent
                    source={articleBody}
                  />
                )}
          </div>


          {/* ===============================================
              Related articles
              =============================================== */}

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
                {relatedPosts.map(
                  (
                    relatedPost,
                  ) => {
                    const formattedDate =
                      new Intl.DateTimeFormat(
                        "ja-JP",
                        {
                          year: "numeric",
                          month: "2-digit",
                          day: "2-digit",
                        },
                      ).format(
                        new Date(
                          relatedPost.date,
                        ),
                      );

                    return (
                      <Link
                        className="related-post-card"
                        href={
                          `/blog/${relatedPost.slug}`
                        }
                        key={
                          relatedPost.slug
                        }
                      >
                        <div className="related-post-image">
                          <Image
                            src={
                              relatedPost.image
                            }
                            alt={
                              `${relatedPost.title}のアイキャッチ画像`
                            }
                            fill
                            sizes="(max-width: 700px) 100vw, 33vw"
                          />
                        </div>

                        <div className="related-post-body">

                          <div className="related-post-meta">
                            <span>
                              {
                                relatedPost.category
                              }
                            </span>

                            <time
                              dateTime={
                                relatedPost.date
                              }
                            >
                              {
                                formattedDate
                              }
                            </time>
                          </div>

                          <h3>
                            <ArticleTitle
                              title={
                                relatedPost.title
                              }
                              lines={
                                relatedPost.cardTitleLines
                              }
                            />
                          </h3>

                          <p>
                            {
                              relatedPost.description
                            }
                          </p>

                          <span className="related-post-link">
                            記事を読む →
                          </span>
                        </div>
                      </Link>
                    );
                  },
                )}
              </div>
            </section>
          )}

        </article>
      </main>
    </>
  );
}
