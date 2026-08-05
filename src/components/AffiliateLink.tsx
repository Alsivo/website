"use client";

import type {
  MouseEvent,
  ReactNode,
} from "react";

type AffiliateLinkProps = {
  href: string;
  service: string;
  linkType?: "affiliate" | "official";
  network?: string;
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
  children,
}: AffiliateLinkProps) {
  const handleClick = (
    event: MouseEvent<HTMLAnchorElement>,
  ) => {
    console.log("clicked");

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
    <a
      className={[
        "affiliate-cta-link",
        linkType === "affiliate"
          ? "affiliate-cta-link-paid"
          : "affiliate-cta-link-official",
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
      {children}
    </a>
  );
}