type ArticleTitleProps = {
  title: string;
  lines?: string[];
};

export default function ArticleTitle({
  title,
  lines,
}: ArticleTitleProps) {
  if (!lines || lines.length === 0) {
    return <>{title}</>;
  }

  return (
    <>
      {lines.map((line, index) => (
        <span key={`${line}-${index}`}>
          {line}
          {index < lines.length - 1 && <br />}
        </span>
      ))}
    </>
  );
}