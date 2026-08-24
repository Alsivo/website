import Image from "next/image";
import type { ReactNode } from "react";

type Speaker = "al" | "cibo";

const portraits: Record<Speaker, Record<string, string>> = {
  al: {
    worried: "/images/characters/al-worried.png",
    surprised: "/images/characters/al-surprised.png",
    happy: "/images/characters/al-happy.png",
    sad: "/images/characters/al-sad.png",
    thinking: "/images/characters/al-thinking.png",
    determined: "/images/characters/al-determined.png",
    default: "/images/characters/al-upper-body-v1.png",
  },
  cibo: {
    concerned: "/images/characters/cibo-concerned.png",
    surprised: "/images/characters/cibo-surprised.png",
    happy: "/images/characters/cibo-happy.png",
    empathetic: "/images/characters/cibo-empathetic.png",
    thinking: "/images/characters/cibo-thinking.png",
    recommend: "/images/characters/cibo-recommend.png",
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
      <div className="character-dialogue-person">
        <div className="character-dialogue-portrait">
          <Image src={src} alt={`${name}の表情`} fill sizes="88px" />
        </div>
        <span className="character-dialogue-name">{name}</span>
      </div>
      <div className="character-dialogue-body">
        <div className="character-dialogue-bubble">{children}</div>
      </div>
    </div>
  );
}
