import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Script from "next/script";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "ALSIVO",
    template: "%s | ALSIVO",
  },

  description:
    "AIツール、生成AI、仕事効率化に関する実践的な情報を発信するAIメディア。",

  openGraph: {
    siteName: "ALSIVO",
    title: "ALSIVO",
    description:
      "AIツール、生成AI、仕事効率化に関する実践的な情報を発信するAIメディア。",
    type: "website",
    url: "https://www.alsivo.com",
  },

  alternates: {
    types: {
      "application/rss+xml":
        "https://www.alsivo.com/rss.xml",
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ja"
      data-scroll-behavior="smooth"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <meta
          name="impact-site-verification"
          {...{
            value: "e1b1347b-5614-46cc-b69d-047b228a9dac",
          }}
        />
      </head>
      <body className="min-h-full flex flex-col">
        <Header />

        {children}

        <Footer />

        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-T4WGR44WB2"
          strategy="afterInteractive"
        />

        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-T4WGR44WB2');
          `}
        </Script>
      </body>
    </html>
  );
}