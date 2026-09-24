import Link from "next/link";

import Rail from "./Rail";

export default function Section({
  title,
  subtitle,
  link,
  railClassName,
  children,
}: {
  title: string;
  subtitle?: string;
  link?: string;
  railClassName?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="section reveal">
      <div className="container">
        <div className="section__head">
          <div>
            <h2 className="section__title">{title}</h2>
            {subtitle && (
              <p className="muted" style={{ marginTop: "var(--s-1)" }}>
                {subtitle}
              </p>
            )}
          </div>
          {link && (
            <Link className="section__link" href={link}>
              Barchasini ko&apos;rish →
            </Link>
          )}
        </div>

        <Rail className={railClassName}>{children}</Rail>
      </div>
    </section>
  );
}
