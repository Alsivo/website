import Link from "next/link";

export default function Header() {
  return (
    <header className="site-header">
      <Link className="brand" href="/" aria-label="Alsivo ホーム">
        <span className="brand-mark" aria-hidden="true">
          A
        </span>
        <span>Alsivo</span>
      </Link>

      <nav className="navigation" aria-label="メインナビゲーション">
        <Link href="/about">About</Link>
        <Link href="/blog">Blog</Link>
        <Link href="/tools">Tools</Link>
        <Link href="/contact">Contact</Link>
      </nav>
    </header>
  );
}