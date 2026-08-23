import Image from "next/image";
import Link from "next/link";
import { getAllBlogPosts } from "../lib/blog";
import ArticleTitle from "../components/ArticleTitle";
import {
  createWebsiteJsonLd,
  serializeJsonLd,
} from "@/lib/structured-data";

const categoryLinks = [
  {
    label: "料金・プラン比較",
    keyword: "料金",
  },
  {
    label: "文章作成",
    keyword: "文章",
  },
  {
    label: "画像生成",
    keyword: "画像",
  },
  {
    label: "資料作成",
    keyword: "プレゼン",
  },
  {
    label: "コード生成",
    keyword: "コード",
  },
  {
    label: "AIツール比較",
    keyword: "比較",
  },
];


export default function Home() {
  const articles = getAllBlogPosts();

  const featuredArticles = articles.slice(0, 3);

  const latestArticles = articles.slice(0, 6);

  const websiteJsonLd = createWebsiteJsonLd();
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: serializeJsonLd(
            websiteJsonLd,
          ),
        }}
      />

      <main>
        <section className="media-hero">
          <div className="media-hero-content">
            <p className="eyebrow">
              AI TOOLS & PRACTICAL GUIDES
            </p>

            <h1>
              <span>AIを</span>
              <br />
              <span>もっとわかりやすく。</span>
              <br />
              <span>もっと実践的に。</span>
            </h1>

            <p className="media-hero-description">
              <span className="desktop-copy">
                <span className="copy-line">AIツールや生成AIに関する情報を、分かりやすく実践的に。</span>
                <br />
                <span className="copy-line">「結局どれを選べばいいのか」「生活や仕事でどう使えばいいのか」を整理して届けます。</span>
              </span>
              <span className="mobile-copy">
                <span className="copy-line">AIツールや生成AIに関する情報を、</span>
                <br />
                <span className="copy-line">分かりやすく実践的に。「結局どれを選べばいいのか」</span>
                <br />
                <span className="copy-line">「生活や仕事でどう使えばいいのか」</span>
                <br />
                <span className="copy-line">を整理して届けます。</span>
              </span>
            </p>

            <div className="media-hero-actions">
              <Link
                className="button button-primary"
                href="/blog"
              >
                記事を探す
                <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>

          <div
            className="media-hero-orb"
            aria-hidden="true"
          />
        </section>

        {featuredArticles.length > 0 && (
          <section className="home-section home-featured">
            <div className="home-section-heading">
              <div>
                <p className="section-kicker">
                  FEATURED
                </p>

                <h2>
                  まず読んでほしい記事
                </h2>
              </div>

              <Link href="/blog">
                すべての記事を見る →
              </Link>
            </div>

            <div className="home-featured-grid">
              {featuredArticles.map(
                (article, index) => (
                  <Link
                    className={
                      index === 0
                        ? "home-featured-card home-featured-card-main"
                        : "home-featured-card"
                    }
                    href={`/blog/${article.slug}`}
                    key={article.slug}
                  >
                    <div className="home-featured-image">
                      <Image
                        src={article.image}
                        alt={`${article.title}のアイキャッチ画像`}
                        fill
                        sizes={
                          index === 0
                            ? "(max-width: 900px) 100vw, 66vw"
                            : "(max-width: 900px) 100vw, 33vw"
                        }
                      />

                      <span>
                        {article.category}
                      </span>
                    </div>

                    <div className="home-featured-body">
                      <h3>
                        <ArticleTitle
                          title={article.title}
                          lines={article.cardTitleLines}
                        />
                      </h3>

                      <p>
                        {article.description}
                      </p>

                      <span className="home-card-link">
                        記事を読む →
                      </span>
                    </div>
                  </Link>
                ),
              )}
            </div>
          </section>
        )}

        <section className="home-section home-discovery">
          <div className="home-section-heading">
            <div>
              <p className="section-kicker">
                DISCOVER
              </p>

              <h2>
                目的から探す
              </h2>
            </div>
          </div>

          <div className="home-category-grid">
            {categoryLinks.map((item) => (
              <Link
                href="/blog"
                className="home-category-card"
                key={item.label}
              >
                <span>{item.label}</span>

                <span aria-hidden="true">
                  →
                </span>
              </Link>
            ))}
          </div>
        </section>

        {latestArticles.length > 0 && (
          <section className="home-section home-latest">
            <div className="home-section-heading">
              <div>
                <p className="section-kicker">
                  LATEST
                </p>

                <h2>
                  最新の記事
                </h2>
              </div>

              <Link href="/blog">
                記事一覧へ →
              </Link>
            </div>

            <div className="home-latest-grid">
              {latestArticles.map(
                (article) => (
                  <Link
                    className="home-latest-card"
                    href={`/blog/${article.slug}`}
                    key={article.slug}
                  >
                    <div className="home-latest-image">
                      <Image
                        src={article.image}
                        alt={`${article.title}のアイキャッチ画像`}
                        fill
                        sizes="(max-width: 700px) 100vw, 33vw"
                      />
                    </div>

                    <div className="home-latest-body">
                      <span className="home-latest-category">
                        {article.category}
                      </span>

                      <h3>
                        {article.title}
                      </h3>

                      <p>
                        {article.description}
                      </p>
                    </div>
                  </Link>
                ),
              )}
            </div>
          </section>
        )}

        <section className="home-about">
          <div>
            <p className="section-kicker">
              ABOUT ALSIVO
            </p>
            <h2>
              <span>AIを</span>
              <br className="mobile-about-break" />
              <span>あなたの生活の</span>
              <br />
              <span>一番身近な味方へ。</span>
            </h2>
          </div>

          <div className="home-about-copy">
            <p>
              <span className="copy-line">ALSIVOは、AIツールや生成AIに関する情報を、</span>
              <br />
              <span className="copy-line">分かりやすく実践的に届けるメディアです。</span>
            </p>

            <p>
              <span className="copy-line">新しい技術をただ紹介するのではなく、</span>
              <br />
              <span className="copy-line">「結局どれを選べばいいのか」</span>
              <br />
              <span className="copy-line">「生活</span>
              <br />
              <span className="copy-line">や仕事でどう使えばいいのか」</span>
              <br />
              <span className="copy-line">を、初めて使う人にも伝わる形で整理します。</span>
            </p>

          </div>
        </section>

        <p
          style={{
            fontSize: "10px",
            opacity: 0.35,
            textAlign: "center",
            padding: "8px 16px",
            margin: 0,
          }}
        >
          Impact-Site-Verification:
          e1b1347b-5614-46cc-b69d-047b228a9dac
        </p>
      </main>
    </>
  );
}
