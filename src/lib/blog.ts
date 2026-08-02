import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import type {
  BlogPost,
  BlogPostFrontmatter,
  BlogPostSummary,
} from "../types/blog";

const BLOG_DIRECTORY = path.join(process.cwd(), "content", "blog");

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