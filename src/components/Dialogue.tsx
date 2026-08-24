import Image from "next/image";
import type { ReactNode } from "react";

type Speaker = "al" | "cibo";

const portraits: Record<Speaker, Record<string, string>> = {
  al: {
    worried: "/images/characters/al-upper-body-v1.png",
    surprised: "/images/characters/al-upper-body-v1.png",
    happy: "/images/characters/al-upper-body-v1.png",
    sad: "/images/characters/al-upper-body-v1.png",
    thinking: "/images/characters/al-upper-body-v1.png",
    determined: "/images/characters/al-upper-body-v1.png",
    default: "/images/characters/al-upper-body-v1.png",
  },
  cibo: {
    concerned: "/images/characters/cibo-upper-body-v1.png",
    surprised: "/images/characters/cibo-upper-body-v1.png",
    happy: "/images/characters/cibo-upper-body-v1.png",
    empathetic: "/images/characters/cibo-upper-body-v1.png",
    thinking: "/images/characters/cibo-upper-body-v1.png",
    recommend: "/images/characters/cibo-upper-body-v1.png",
    default: "/images/characters/cibo-upper-body-v1.png",
  },
};

export default function Dialogue({
  speaker,
  emotion = "default",
  children,
}: {
  speaker: Speaker;
  emotion?: string;
  children: ReactNode;
}) {
  const name = speaker === "al" ? "アル" : "シーボ";
  const src = portraits[speaker][emotion] ?? portraits[speaker].default;

  return (
    <div className={`character-dialogue character-dialogue-${speaker}`}>
      <div className="character-dialogue-portrait">
        <Image src={src} alt={`${name}の表情`} fill sizes="88px" />
      </div>
      <div className="character-dialogue-body">
        <span className="character-dialogue-name">{name}</span>
        <div className="character-dialogue-bubble">{children}</div>
      </div>
    </div>
  );
}
