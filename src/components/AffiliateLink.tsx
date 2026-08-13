"use client";

import type {
  MouseEvent,
  ReactNode,
} from "react";

type CtaType =
  | "primary"
  | "comparison"
  | "secondary";

type AffiliateLinkProps = {
  href: string;
  service: string;
  linkType?: "affiliate" | "official";
  network?: string;
  ctaType?: CtaType;
  ctaPlacement?:
    | "after_toc"
    | "after_comparison"
    | "before_faq";
  children: ReactNode;
};

type GtagFunction = (
  command: "event",
  eventName: string,
  parameters: Record<
    string,
    string | number | boolean
  >,
) => void;

type WindowWithGtag = Window & {
  gtag?: GtagFunction;
};

export default function AffiliateLink({
  href,
  service,
  linkType = "official",
  network = "none",
  ctaType = "primary",
  ctaPlacement = "before_faq",
  children,
}: AffiliateLinkProps) {
  const handleClick = (
    event: MouseEvent,
  ) => {

    const currentWindow =
      window as WindowWithGtag;

    const ctaLabel =
      event.currentTarget.textContent?.trim()
      ?? "";

    if (
      typeof currentWindow.gtag
      === "function"
    ) {
      currentWindow.gtag(
        "event",
        "affiliate_click",
        {
          service_name: service,
          link_type: linkType,
          affiliate_network: network,
          cta_type: ctaType,
          cta_placement: ctaPlacement,
          link_url: href,
          page_path:
            window.location.pathname,
          page_title: document.title,
          cta_label: ctaLabel,
          transport_type: "beacon",
        },
      );
    }
  };

  return (
    <div
      className={[
        "affiliate-cta-card",
        `affiliate-cta-card-${ctaType}`,
      ].join(" ")}
    >
      <div className="affiliate-cta-card-content">
        <p className="affiliate-cta-eyebrow">
          公式情報を確認
        </p>

        <p className="affiliate-cta-service">
          {service}
        </p>

        <p className="affiliate-cta-description">
          料金や利用条件は変更されることがあります。
          契約・登録前に公式サイトで最新情報をご確認ください。
        </p>
      </div>

      <a
        className={[
          "affiliate-cta-link",
          linkType === "affiliate"
            ? "affiliate-cta-link-paid"
            : "affiliate-cta-link-official",
          `affiliate-cta-link-${ctaType}`,
        ].join(" ")}
        href={href}
        onClick={handleClick}
        rel={
          linkType === "affiliate"
            ? "sponsored nofollow noopener noreferrer"
            : "noopener noreferrer"
        }
        target="_blank"
      >
        <span>{children}</span>
        <span
          className="affiliate-cta-arrow"
          aria-hidden="true"
        >
          ↗
        </span>
      </a>

      {linkType === "affiliate" && (
        <p className="affiliate-cta-disclosure">
          このリンクには広告が含まれます
        </p>
      )}
    </div>
  );
}