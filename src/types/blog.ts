export type BlogFaqItem = {
  question: string;
  answer: string;
};

export type BlogPostFrontmatter = {
  title: string;
  titleLines?: string[];
  cardTitleLines?: string[];
  description: string;
  date: string;
  updated?: string;
  verified?: string;
  category: string;
  tags: string[];
  readingTime: string;
  image: string;
  faq: BlogFaqItem[];
  published: boolean;
};

export type BlogPostSummary = BlogPostFrontmatter & {
  slug: string;
};

export type BlogPost = BlogPostSummary & {
  content: string;
};