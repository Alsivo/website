export type BlogPostFrontmatter = {
  title: string;
  description: string;
  date: string;
  updated?: string;
  category: string;
  tags: string[];
  readingTime: string;
  published: boolean;
};

export type BlogPostSummary = BlogPostFrontmatter & {
  slug: string;
};

export type BlogPost = BlogPostSummary & {
  content: string;
};