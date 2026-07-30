import Link from "next/link";

export default function Footer() {
  return (
    <footer className="footer">
      <Link className="brand footer-brand" href="/">
        <span className="brand-mark" aria-hidden="true">
          A
        </span>
        <span>Alsivo</span>
      </Link>

      <p>AIを、あなたの仕事の一番身近な味方へ。</p>

      <div className="footer-links">
        <Link href="/about">About</Link>
        <Link href="/blog">Blog</Link>
        <Link href="/tools">Tools</Link>
        <Link href="/contact">Contact</Link>
        <Link href="/privacy">Privacy</Link>
        <Link href="/terms">Terms</Link>
      </div>

      <small>© 2026 Alsivo. All rights reserved.</small>
    </footer>
  );
}