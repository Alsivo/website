import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import type {
  BlogFaqItem,
  BlogPost,
  BlogPostFrontmatter,
  BlogPostSummary,
} from "@/types/blog";

const BLOG_DIRECTORY = path.join(process.cwd(), "content", "blog");

const INTERNAL_LINKS_FILE = path.join(
  process.cwd(),
  "atlas",
  "data",
  "internal_links",
  "internal_links.json",
);

function ensureBlogDirectory(): void {
  if (!fs.existsSync(BLOG_DIRECTORY)) {
    fs.mkdirSync(BLOG_DIRECTORY, { recursive: true });
  }
}

function getMdxFileNames(): string[] {
  ensureBlogDirectory();

  return fs
    .readdirSync(BLOG_DIRECTORY)
    .filter((fileName) => fileName.endsWith(".mdx"));
}

function validateFaq(
  value: unknown,
  fileName: string,
): BlogFaqItem[] {
  if (!Array.isArray(value)) {
    throw new Error(
      `${fileName}: frontmatterの「faq」は配列にしてください。`,
    );
  }

  if (value.length < 3 || value.length > 5) {
    throw new Error(
      `${fileName}: frontmatterの「faq」は3〜5件にしてください。`,
    );
  }

  return value.map((item, index) => {
    if (
      typeof item !== "object" ||
      item === null
    ) {
      throw new Error(
        `${fileName}: faqの${index + 1}件目の形式が不正です。`,
      );
    }

    const faqItem = item as Record<
      string,
      unknown
    >;

    if (
      typeof faqItem.question !== "string" ||
      faqItem.question.trim() === ""
    ) {
      throw new Error(
        `${fileName}: faqの${index + 1}件目の質問が未入力です。`,
      );
    }

    if (
      typeof faqItem.answer !== "string" ||
      faqItem.answer.trim() === ""
    ) {
      throw new Error(
        `${fileName}: faqの${index + 1}件目の回答が未入力です。`,
      );
    }

    return {
      question: faqItem.question.trim(),
      answer: faqItem.answer.trim(),
    };
  });
}

function validateFrontmatter(
  data: Partial<BlogPostFrontmatter>,
  fileName: string,
): BlogPostFrontmatter {
  const requiredStringFields = [
    "title",
    "description",
    "date",
    "category",
    "readingTime",
    "image",
  ] as const;

  for (const field of requiredStringFields) {
    if (typeof data[field] !== "string" || data[field]?.trim() === "") {
      throw new Error(
        `${fileName}: frontmatterの「${field}」が未入力です。`,
      );
    }
  }

  if (!Array.isArray(data.tags)) {
    throw new Error(`${fileName}: frontmatterの「tags」は配列にしてください。`);
  }

  return {
    title: data.title!,
    description: data.description!,
    date: data.date!,
    updated: data.updated,
    category: data.category!,
    tags: data.tags,
    readingTime: data.readingTime!,
    image: data.image!,
    faq: validateFaq(
      data.faq,
      fileName,
    ),
    published: data.published !== false,
  };
}

export function getAllBlogPosts(): BlogPostSummary[] {
  const posts = getMdxFileNames()
    .map((fileName) => {
      const slug = fileName.replace(/\.mdx$/, "");
      const fullPath = path.join(BLOG_DIRECTORY, fileName);
      const fileContents = fs.readFileSync(fullPath, "utf8");
      const { data } = matter(fileContents);
      const frontmatter = validateFrontmatter(data, fileName);

      return {
        slug,
        ...frontmatter,
      };
    })
    .filter((post) => post.published)
    .sort(
      (a, b) =>
        new Date(b.date).getTime() - new Date(a.date).getTime(),
    );

  return posts;
}

export function getBlogPostBySlug(slug: string): BlogPost | null {
  const safeSlug = slug.replace(/[^a-zA-Z0-9-_]/g, "");
  const fullPath = path.join(BLOG_DIRECTORY, `${safeSlug}.mdx`);

  if (!fs.existsSync(fullPath)) {
    return null;
  }

  const fileContents = fs.readFileSync(fullPath, "utf8");
  const { data, content } = matter(fileContents);
  const frontmatter = validateFrontmatter(data, `${safeSlug}.mdx`);

  if (!frontmatter.published) {
    return null;
  }

  return {
    slug: safeSlug,
    ...frontmatter,
    content,
  };
}

export function getAllBlogSlugs(): string[] {
  return getAllBlogPosts().map((post) => post.slug);
}

type InternalLinkItem = {
  slug: string;
  anchor?: string;
  reason?: string;
};

type InternalLinkMap = Record<
  string,
  InternalLinkItem[]
>;

function getInternalLinkMap(): InternalLinkMap {
  if (!fs.existsSync(INTERNAL_LINKS_FILE)) {
    return {};
  }

  try {
    const fileContents = fs.readFileSync(
      INTERNAL_LINKS_FILE,
      "utf8",
    );

    const data = JSON.parse(
      fileContents,
    ) as unknown;

    if (
      typeof data !== "object"
      || data === null
      || Array.isArray(data)
    ) {
      return {};
    }

    return data as InternalLinkMap;
  } catch {
    return {};
  }
}

export function getRelatedBlogPosts(
  currentSlug: string,
  _category: string,
  _tags: string[],
  limit = 3,
): BlogPostSummary[] {
  const internalLinkMap =
    getInternalLinkMap();

  const selectedLinks =
    internalLinkMap[currentSlug] ?? [];

  if (selectedLinks.length === 0) {
    return [];
  }

  const allPosts = getAllBlogPosts();

  const postMap = new Map(
    allPosts.map((post) => [
      post.slug,
      post,
    ]),
  );

  return selectedLinks
    .slice(0, limit)
    .map((link) =>
      postMap.get(link.slug),
    )
    .filter(
      (
        post,
      ): post is BlogPostSummary =>
        post !== undefined
        && post.slug !== currentSlug,
    );
}