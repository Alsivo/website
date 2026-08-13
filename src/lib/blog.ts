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
    updated:
      typeof data.updated === "string"
        ? data.updated
        : undefined,
    verified:
      typeof data.verified === "string"
        ? data.verified
        : undefined,
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

export type ArticleCta = {
  href: string;
  service: string;
  linkType: "affiliate" | "official";
  network: string;
  ctaType: "primary" | "comparison" | "secondary";
  ctaPlacement:
    | "after_toc"
    | "after_comparison"
    | "before_faq";
  label: string;
};

export function extractArticleCta(
  content: string,
  placement: ArticleCta["ctaPlacement"],
): ArticleCta | null {
  const pattern =
    /<AffiliateLink\s+([^>]+)>([\s\S]*?)<\/AffiliateLink>/g;

  let match: RegExpExecArray | null;

  while ((match = pattern.exec(content)) !== null) {
    const attributes = match[1];
    const label = match[2].trim();

    const getAttribute = (
      name: string,
    ): string | null => {
      const attributeMatch =
        attributes.match(
          new RegExp(
            `${name}="([^"]*)"`,
          ),
        );

      return attributeMatch
        ? attributeMatch[1]
        : null;
    };

    const ctaPlacement =
      getAttribute("ctaPlacement");

    if (ctaPlacement !== placement) {
      continue;
    }

    const href = getAttribute("href");
    const service = getAttribute("service");

    if (!href || !service) {
      continue;
    }

    const linkType =
      getAttribute("linkType")
      === "affiliate"
        ? "affiliate"
        : "official";

    const rawCtaType =
      getAttribute("ctaType");

    const ctaType:
      ArticleCta["ctaType"] =
        rawCtaType === "comparison"
          ? "comparison"
          : rawCtaType === "secondary"
            ? "secondary"
            : "primary";

    return {
      href,
      service,
      linkType,
      network:
        getAttribute("network")
        ?? "none",
      ctaType,
      ctaPlacement: placement,
      label,
    };
  }

  return null;
}

export function removeArticleCta(
  content: string,
  placement: ArticleCta["ctaPlacement"],
  ctaType?: ArticleCta["ctaType"],
): string {
  const pattern =
    /<AffiliateLink\s+([^>]+)>[\s\S]*?<\/AffiliateLink>/g;

  return content.replace(
    pattern,
    (fullMatch, attributes: string) => {
      const getAttribute = (
        name: string,
      ): string | null => {
        const match =
          attributes.match(
            new RegExp(
              `${name}="([^"]*)"`,
            ),
          );

        return match
          ? match[1]
          : null;
      };

      const itemPlacement =
        getAttribute("ctaPlacement");

      const itemCtaType =
        getAttribute("ctaType");

      if (itemPlacement !== placement) {
        return fullMatch;
      }

      if (
        ctaType
        && itemCtaType !== ctaType
      ) {
        return fullMatch;
      }

      return "";
    },
  );
}