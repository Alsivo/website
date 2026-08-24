"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";
import type { BlogPostSummary } from "../types/blog";
import ArticleTitle from "./ArticleTitle";

type BlogExplorerProps = {
  articles: BlogPostSummary[];
};

const ALL_FILTER = "all";

export default function BlogExplorer({
  articles,
}: BlogExplorerProps) {
  const [keyword, setKeyword] = useState("");
  const [selectedCategory, setSelectedCategory] =
    useState(ALL_FILTER);
  const [selectedTag, setSelectedTag] = useState(ALL_FILTER);

  const categories = useMemo(() => {
    return Array.from(
      new Set(articles.map((article) => article.category)),
    ).sort((a, b) => a.localeCompare(b, "ja"));
  }, [articles]);

  const tags = useMemo(() => {
    return Array.from(
      new Set(articles.flatMap((article) => article.tags)),
    ).sort((a, b) => a.localeCompare(b, "ja"));
  }, [articles]);

  const filteredArticles = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();

    return articles.filter((article) => {
      const matchesKeyword =
        normalizedKeyword === "" ||
        article.title.toLowerCase().includes(normalizedKeyword) ||
        article.description
          .toLowerCase()
          .includes(normalizedKeyword) ||
        article.category
          .toLowerCase()
          .includes(normalizedKeyword) ||
        article.tags.some((tag) =>
          tag.toLowerCase().includes(normalizedKeyword),
        );

      const matchesCategory =
        selectedCategory === ALL_FILTER ||
        article.category === selectedCategory;

      const matchesTag =
        selectedTag === ALL_FILTER ||
        article.tags.includes(selectedTag);

      return matchesKeyword && matchesCategory && matchesTag;
    });
  }, [articles, keyword, selectedCategory, selectedTag]);

  const hasActiveFilters =
    keyword.trim() !== "" ||
    selectedCategory !== ALL_FILTER ||
    selectedTag !== ALL_FILTER;

  function resetFilters(): void {
    setKeyword("");
    setSelectedCategory(ALL_FILTER);
    setSelectedTag(ALL_FILTER);
  }

  return (
    <>
      <div className="blog-filter-panel">
        <div className="blog-search-field">
          <label htmlFor="blog-search">記事を検索</label>

          <input
            id="blog-search"
            type="search"
            placeholder="タイトル、タグ、キーワード"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
          />
        </div>

        <div className="blog-filter-field">
          <label htmlFor="category-filter">カテゴリー</label>

          <select
            id="category-filter"
            value={selectedCategory}
            onChange={(event) =>
              setSelectedCategory(event.target.value)
            }
          >
            <option value={ALL_FILTER}>すべて</option>

            {categories.map((category: string) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>

        <div className="blog-filter-field">
          <label htmlFor="tag-filter">タグ</label>

          <select
            id="tag-filter"
            value={selectedTag}
            onChange={(event) =>
              setSelectedTag(event.target.value)
            }
          >
            <option value={ALL_FILTER}>すべて</option>

            {tags.map((tag: string) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
        </div>

        <button
          className="blog-filter-reset"
          type="button"
          onClick={resetFilters}
          disabled={!hasActiveFilters}
        >
          条件をリセット
        </button>
      </div>

      <div className="article-list-header">
        <h2>Latest Articles</h2>

        <p>
          {filteredArticles.length}{" "}
          {filteredArticles.length === 1
            ? "Article"
            : "Articles"}
        </p>
      </div>

      {filteredArticles.length === 0 ? (
        <div className="blog-no-results">
          <p>条件に一致する記事がありません。</p>

          <button type="button" onClick={resetFilters}>
            すべての記事を表示
          </button>
        </div>
      ) : (
        <div className="article-card-grid">
          {filteredArticles.map((article) => {
            const formattedDate = new Intl.DateTimeFormat(
              "ja-JP",
              {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
              },
            ).format(new Date(article.date));

            return (
              <Link
                className="article-card"
                href={`/blog/${article.slug}`}
                key={article.slug}
              >
                <div className="article-card-visual">
                  <Image
                    className="article-card-image"
                    src={article.image}
                    alt={`${article.title}のアイキャッチ画像`}
                    fill
                    sizes="(max-width: 800px) 100vw, 50vw"
                  />

                  <div className="article-card-image-overlay" />

                </div>

                <div className="article-card-body">
                  <div className="article-card-meta">
                    <time dateTime={article.date}>
                      {formattedDate}
                    </time>

                    <span>{article.readingTime}</span>
                  </div>

                  <h2>
                    <ArticleTitle
                      title={article.title}
                      lines={article.cardTitleLines}
                    />
                  </h2>

                  <p>{article.description}</p>

                  <div className="article-card-tags">
                    {article.tags
                      .slice(0, 3)
                      .map((tag: string) => (
                        <span key={tag}>{tag}</span>
                      ))}
                  </div>

                  <span className="article-card-link">
                    記事を読む
                    <span aria-hidden="true">→</span>
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </>
  );
}
