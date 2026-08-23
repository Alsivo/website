import Image from "next/image";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-identity">
        <Link
          className="brand footer-brand"
          href="/"
        >
          <Image
            className="brand-mark"
            src="/images/alsivo_icon.jpg"
            alt=""
            width={36}
            height={36}
          />

          <span>ALSIVO</span>
        </Link>
        <p>AIをあなたの生活の一番身近な味方へ。</p>
      </div>

      <nav
        className="footer-links"
        aria-label="フッターナビゲーション"
      >
        <Link href="/blog">
          記事を探す
        </Link>


        <Link href="/privacy">
          Privacy
        </Link>

        <Link href="/terms">
          Terms
        </Link>
      </nav>

      <small>
        © 2026 ALSIVO. All rights reserved.
      </small>
    </footer>
  );
}
