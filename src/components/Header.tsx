import Image from "next/image";
import Link from "next/link";

export default function Header() {
  return (
    <header className="site-header">
      <Link
        className="brand"
        href="/"
        aria-label="ALSIVO トップページ"
      >
        <Image
          className="brand-mark"
          src="/images/alsivo_icon.jpg"
          alt=""
          width={36}
          height={36}
          priority
        />

        <span>ALSIVO</span>
      </Link>

      <nav
        className="navigation"
        aria-label="メインナビゲーション"
      >
        <Link href="/">
          Top
        </Link>

        <Link href="/blog">
          記事を探す
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
