import createMDX from "@next/mdx";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  pageExtensions: ["js", "jsx", "md", "mdx", "ts", "tsx"],
  transpilePackages: ["next-mdx-remote"],
  async redirects() {
    return [
      {
        source: "/blog/ai-blogkun-gold-reputation-guide",
        destination: "/blog/ai-blogkun-gold-reputation-safety-pricing",
        permanent: true,
      },
      {
        source: "/blog/ai-blogkun-gold-reputation-review",
        destination: "/blog/ai-blogkun-gold-reputation-safety-pricing",
        permanent: true,
      },
      {
        source: "/blog/ai-blogkun-gold-reputation",
        destination: "/blog/ai-blogkun-gold-reputation-safety-pricing",
        permanent: true,
      },
      {
        source: "/blog/ai-minutes-tool-comparison-notta",
        destination: "/blog/ai-minutes-tools-comparison-notta",
        permanent: true,
      },
      {
        source: "/blog/notta-reputation-guide",
        destination: "/blog/notta-reputation-workflow-guide",
        permanent: true,
      },
      {
        source: "/blog/notta-reputation-setup-pricing",
        destination: "/blog/notta-reputation-workflow-guide",
        permanent: true,
      },
      {
        source: "/blog/notta-reputation-usage-pricing-security",
        destination: "/blog/notta-reputation-workflow-guide",
        permanent: true,
      },
      {
        source: "/blog/notta-reputation",
        destination: "/blog/notta-reputation-workflow-guide",
        permanent: true,
      },
      {
        source: "/blog/gamma-reputation-pricing",
        destination: "/blog/gamma-reputation",
        permanent: true,
      },
      {
        source: "/blog/dmm-genai-camp-reviews",
        destination: "/blog/dmm-genai-camp-reputation-roadmap",
        permanent: true,
      },
      {
        source: "/blog/value-ai-writer-reputation-review",
        destination: "/blog/value-ai-writer-review-trial-guide",
        permanent: true,
      },
      {
        source: "/blog/gemini-pricing-plan-comparison",
        destination: "/blog/gemini-pricing-plans-jp-decision",
        permanent: true,
      },
      {
        source: "/blog/claude-pricing-plans-comparison-pro-max",
        destination: "/blog/claude-pricing-plans-guide",
        permanent: true,
      },
      {
        source: "/blog/claude-free-pro-team-pricing",
        destination: "/blog/claude-pricing-plans-guide",
        permanent: true,
      },
      {
        source: "/blog/claude-usage-limit-reset",
        destination: "/blog/claude-pricing-plans-guide",
        permanent: true,
      },
      {
        source: "/blog/deepl-pricing-plans-guide",
        destination: "/blog/deepl-reputation-security-guide",
        permanent: true,
      },
      {
        source: "/blog/aidd-reputation-corporate-training",
        destination: "/blog/aidd-reputation-guide",
        permanent: true,
      },
      {
        source: "/blog/bun-ken-review-price-security-workflow",
        destination: "/blog/bunken-reputation-pricing-security-guide",
        permanent: true,
      },
      {
        source: "/blog/bunken-reputation",
        destination: "/blog/bunken-reputation-pricing-security-guide",
        permanent: true,
      },
      {
        source: "/blog/ai-video-generator-tools-comparison-pricing-usage",
        destination: "/blog/ai-video-tools-compare-pick-two",
        permanent: true,
      },
    ];
  },
};

const withMDX = createMDX({
  extension: /\.(md|mdx)$/,
});

export default withMDX(nextConfig);
