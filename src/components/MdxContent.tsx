import type { ComponentPropsWithoutRef } from "react";
import { MDXRemote } from "next-mdx-remote/rsc";

type MdxContentProps = {
  source: string;
};

const components = {
  h2: (props: ComponentPropsWithoutRef<"h2">) => (
    <h2 className="article-heading" {...props} />
  ),

  h3: (props: ComponentPropsWithoutRef<"h3">) => (
    <h3 className="article-subheading" {...props} />
  ),

  p: (props: ComponentPropsWithoutRef<"p">) => (
    <p className="article-paragraph" {...props} />
  ),

  ul: (props: ComponentPropsWithoutRef<"ul">) => (
    <ul className="article-list" {...props} />
  ),

  ol: (props: ComponentPropsWithoutRef<"ol">) => (
    <ol className="article-list" {...props} />
  ),

  blockquote: (props: ComponentPropsWithoutRef<"blockquote">) => (
    <blockquote className="article-quote" {...props} />
  ),

  a: (props: ComponentPropsWithoutRef<"a">) => (
    <a
      className="article-link"
      rel="noopener noreferrer"
      target="_blank"
      {...props}
    />
  ),
};

export default function MdxContent({ source }: MdxContentProps) {
  return <MDXRemote source={source} components={components} />;
}