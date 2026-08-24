import Image from "next/image";
import Link from "next/link";
import { getAllBlogPosts } from "../lib/blog";
import ArticleSidebar from "../components/ArticleSidebar";
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

  const latestArticles = articles.slice(0, 4);
  const popularArticles = articles.slice(0, 4);

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

          <div className="media-hero-characters" aria-label="アルとシーボの紹介">
            <div className="hero-character-card hero-character-al">
              <div className="hero-character-image"><Image src="/images/characters/al-upper-body-v1.png" alt="アル" fill sizes="240px" /></div>
              <p><strong>アル</strong><span>毎日悩みが尽きない女の子<br />いつもシーボに相談している</span></p>
            </div>
            <div className="hero-character-card hero-character-cibo">
              <div className="hero-character-image"><Image src="/images/characters/cibo-upper-body-v1.png" alt="シーボ" fill sizes="240px" /></div>
              <p><strong>シーボ</strong><span>アルの幼馴染の男の子<br />アルの相談を受けるのが日課</span></p>
            </div>
          </div>
        </section>

        <div className="home-content-with-sidebar">
        <div className="home-main-content">
        {latestArticles.length > 0 && (
          <section className="home-section home-latest">
          <div className="home-section-heading">
            <div>
              <p className="section-kicker">
                  LATEST
              </p>

              <h2>
                最新記事
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

        {popularArticles.length > 0 && (
          <section className="home-section home-popular">
            <div className="home-section-heading">
              <div><p className="section-kicker">POPULAR</p><h2>人気記事</h2></div>
              <Link href="/blog">記事一覧へ →</Link>
            </div>
            <div className="home-latest-grid">
              {popularArticles.map((article) => (
                <Link className="home-latest-card" href={`/blog/${article.slug}`} key={article.slug}>
                  <div className="home-latest-image"><Image src={article.image} alt={`${article.title}のアイキャッチ画像`} fill sizes="(max-width: 700px) 100vw, 33vw" /></div>
                  <div className="home-latest-body"><span className="home-latest-category">{article.category}</span><h3>{article.title}</h3><p>{article.description}</p></div>
                </Link>
              ))}
            </div>
          </section>
        )}

        <section className="home-section home-discovery">
          <div className="home-section-heading"><div><p className="section-kicker">DISCOVER</p><h2>目的から探す</h2></div></div>
          <div className="home-category-grid">
            {categoryLinks.map((item) => (
              <Link href="/blog" className="home-category-card" key={item.label}><span>{item.label}</span><span aria-hidden="true">→</span></Link>
            ))}
          </div>
        </section>

        <section className="home-about">
          <div className="home-about-heading">
            <p className="section-kicker">
              ABOUT ALSIVO
            </p>
            <h2>AIをあなたの生活の一番身近な味方へ。</h2>
          </div>
          <div className="home-about-character home-about-al">
            <div className="home-about-portrait"><Image src="/images/characters/al-upper-body-v1.png" alt="アル" fill sizes="140px" /></div>
            <p>ALSIVOは、AIツールや生成AIに関する情報を、分かりやすく実践的に届けるメディアです。</p>
          </div>
          <div className="home-about-character home-about-cibo">
            <div className="home-about-portrait"><Image src="/images/characters/cibo-upper-body-v1.png" alt="シーボ" fill sizes="150px" /></div>
            <p>新しい技術をただ紹介するのではなく、「結局どれを選べばいいのか」「生活や仕事でどう使えばいいのか」を、初めて使う人にも伝わる形で整理します。</p>
          </div>
        </section>
        </div>
        <ArticleSidebar popular={articles.slice(0, 5)} latest={articles.slice(0, 5)} />
        </div>

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
