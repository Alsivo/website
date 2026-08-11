import Link from "next/link";

export default function Header() {
  return (
    <header className="site-header">
      <Link
        className="brand"
        href="/"
        aria-label="Alsivo トップページ"
      >
        <span
          className="brand-mark"
          aria-hidden="true"
        >
          A
        </span>

        <span>Alsivo</span>
      </Link>

      <nav
        className="navigation"
        aria-label="メインナビゲーション"
      >
        <Link href="/blog">
          記事を探す
        </Link>

        <Link href="/about">
          About
        </Link>
      </nav>

      <Link
        className="header-blog-link"
        href="/blog"
      >
        記事を探す
        <span aria-hidden="true">→</span>
      </Link>
    </header>
  );
}