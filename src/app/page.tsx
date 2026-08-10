const services = [
  {
    number: "01",
    title: "AI Knowledge",
    description:
      "AIツールの選び方や活用方法を、実践的で分かりやすい情報として届けます。",
    status: "Coming soon",
  },
  {
    number: "02",
    title: "AI Tools",
    description:
      "日々の仕事を効率化し、誰でもすぐに使えるシンプルなAIツールを提供します。",
    status: "Coming soon",
  },
  {
    number: "03",
    title: "AI Services",
    description:
      "AIを活用した仕組みやサービスを通して、仕事の新しい選択肢をつくります。",
    status: "Coming soon",
  },
];

export default function Home() {
  return (
    <main>
      <section className="hero" id="top">
        <div className="hero-glow hero-glow-one" aria-hidden="true" />
        <div className="hero-glow hero-glow-two" aria-hidden="true" />

        <div className="hero-content">
          <p className="eyebrow">AI FOR EVERYDAY WORK</p>

          <h1>
            AIを、
            <br />
            あなたの仕事の
            <br />
            <span>一番身近な味方へ。</span>
          </h1>

          <p className="hero-description">
            Alsivoは、AIに関する情報・ツール・サービスを通して、
            <br className="desktop-break" />
            誰もがAIを自然に活用できる未来をつくります。
          </p>

          <div className="hero-actions">
            <a className="button button-primary" href="#services">
              Alsivoについて
              <span aria-hidden="true">→</span>
            </a>

            <a className="button button-secondary" href="#services">
              サービスを見る
            </a>
          </div>
        </div>

        <div className="scroll-guide" aria-hidden="true">
          <span>SCROLL</span>
          <div />
        </div>
      </section>

      <section className="mission section" id="mission">
        <div className="section-label">
          <span>01</span>
          <p>MISSION</p>
        </div>

        <div className="mission-content">
          <p className="section-kicker">AIをもっと身近に。</p>

          <h2>
            技術を意識せず、
            <br />
            誰もがAIの力を活かせる社会へ。
          </h2>

          <div className="mission-copy">
            <p>
              AIは、一部の専門家だけが使う特別な技術ではありません。
              調べる、考える、つくる、伝える。日々の仕事のあらゆる場面で、
              人の可能性を広げる存在になりつつあります。
            </p>

            <p>
              Alsivoは、複雑なAIを分かりやすく、使いやすく届けます。
              AIが人に代わるのではなく、人の仕事を支える最も身近なパートナーになる。
              そんな未来を目指します。
            </p>
          </div>
        </div>
      </section>

      <section className="services section" id="services">
        <div className="section-heading">
          <div className="section-label">
            <span>02</span>
            <p>WHAT WE DO</p>
          </div>

          <div>
            <p className="section-kicker">知る。使う。広げる。</p>
            <h2>AIを仕事につなげる、3つのアプローチ。</h2>
          </div>
        </div>

        <div className="service-grid">
          {services.map((service) => (
            <article className="service-card" key={service.number}>
              <div className="service-card-top">
                <span className="service-number">{service.number}</span>
                <span className="service-status">{service.status}</span>
              </div>

              <div>
                <h3>{service.title}</h3>
                <p>{service.description}</p>
              </div>

              <span className="service-arrow" aria-hidden="true">
                ↗
              </span>
            </article>
          ))}
        </div>
      </section>

      <section className="statement section">
        <p>OUR VISION</p>

        <h2>
          Human potential,
          <br />
          amplified by AI.
        </h2>

        <span>人の可能性を、AIでもっと大きく。</span>
      </section>

      <section className="contact section" id="contact">
        <div>
          <p className="section-kicker">CONTACT</p>
          <h2>
            Alsivoのこれからに、
            <br />
            ご期待ください。
          </h2>
        </div>

        <p>
          AIメディア、AIツール、サービスを順次公開予定です。
          <br />
          お問い合わせページも近日公開します。
        </p>
      </section>

      <p
        style={{
          fontSize: "10px",
          opacity: 0.35,
          textAlign: "center",
          padding: "8px 16px",
          margin: 0,
        }}
      >
        Impact-Site-Verification: 34354601-c219-4542-a128-a042a3086334
      </p>
    </main>
  );
}