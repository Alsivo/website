import type {
  ComponentPropsWithoutRef,
} from "react";
import { MDXRemote } from "next-mdx-remote/rsc";
import AffiliateLink from "./AffiliateLink";
import { createHeadingId } from "../lib/headings";
import remarkGfm from "remark-gfm";

type MdxContentProps = {
  source: string;
};

const components = {
  AffiliateLink,

  h2: ({
    children,
    ...props
  }: ComponentPropsWithoutRef<"h2">) => {
    const headingText = String(children);

    return (
      <h2
        id={createHeadingId(headingText)}
        className="article-heading article-anchor-heading"
        {...props}
      >
        {children}
      </h2>
    );
  },

  h3: ({
    children,
    ...props
  }: ComponentPropsWithoutRef<"h3">) => {
    const headingText = String(children);

    return (
      <h3
        id={createHeadingId(headingText)}
        className="article-subheading article-anchor-heading"
        {...props}
      >
        {children}
      </h3>
    );
  },

  p: (
    props: ComponentPropsWithoutRef<"p">,
  ) => (
    <p
      className="article-paragraph"
      {...props}
    />
  ),

  ul: (
    props: ComponentPropsWithoutRef<"ul">,
  ) => (
    <ul
      className="article-list"
      {...props}
    />
  ),

  ol: (
    props: ComponentPropsWithoutRef<"ol">,
  ) => (
    <ol
      className="article-list"
      {...props}
    />
  ),

  blockquote: (
    props: ComponentPropsWithoutRef<
      "blockquote"
    >,
  ) => (
    <blockquote
      className="article-quote"
      {...props}
    />
  ),

  table: (
    props: ComponentPropsWithoutRef<"table">,
  ) => (
    <div
      className="article-table-wrapper"
      role="region"
      aria-label="比較表"
      tabIndex={0}
    >
      <table
        className="article-table"
        {...props}
      />
    </div>
  ),

  thead: (
    props: ComponentPropsWithoutRef<"thead">,
  ) => (
    <thead
      className="article-table-head"
      {...props}
    />
  ),

  th: (
    props: ComponentPropsWithoutRef<"th">,
  ) => (
    <th
      className="article-table-header"
      {...props}
    />
  ),

  td: (
    props: ComponentPropsWithoutRef<"td">,
  ) => (
    <td
      className="article-table-cell"
      {...props}
    />
  ),

  a: (
    props: ComponentPropsWithoutRef<"a">,
  ) => (
    <a
      className="article-link"
      rel="noopener noreferrer"
      target="_blank"
      {...props}
    />
  ),
};

export default function MdxContent({
  source,
}: MdxContentProps) {
  return (
    <MDXRemote
      source={source}
      components={components}
      options={{
        mdxOptions: {
          remarkPlugins: [remarkGfm],
        },
      }}
    />
  );
}