import Link from "next/link";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-identity">
        <Link
          className="brand footer-brand"
          href="/"
        >
          <span
            className="brand-mark"
            aria-hidden="true"
          >
            A
          </span>

          <span>Alsivo</span>
        </Link>

        <p>
          AIをあなたの仕事の
          一番身近な味方へ。
        </p>
      </div>

      <nav
        className="footer-links"
        aria-label="フッターナビゲーション"
      >
        <Link href="/blog">
          記事を探す
        </Link>

        <Link href="/about">
          Alsivoについて
        </Link>

        <Link href="/privacy">
          Privacy
        </Link>

        <Link href="/terms">
          Terms
        </Link>
      </nav>

      <small>
        © 2026 Alsivo. All rights reserved.
      </small>
    </footer>
  );
}