import type { MDXComponents } from "mdx/types";

const components: MDXComponents = {
  h2: ({ children }) => <h2 className="article-heading">{children}</h2>,

  h3: ({ children }) => <h3 className="article-subheading">{children}</h3>,

  p: ({ children }) => <p className="article-paragraph">{children}</p>,

  ul: ({ children }) => <ul className="article-list">{children}</ul>,

  ol: ({ children }) => <ol className="article-list">{children}</ol>,

  blockquote: ({ children }) => (
    <blockquote className="article-quote">{children}</blockquote>
  ),

  a: ({ href, children }) => (
    <a className="article-link" href={href}>
      {children}
    </a>
  ),
};

export function useMDXComponents(): MDXComponents {
  return components;
}