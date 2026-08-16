import type { ReactNode } from "react";

export function Card({
  title,
  subtitle,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`bg-slate-900 border border-slate-800 rounded-xl p-5 ${className}`}
    >
      {title && (
        <h2 className="text-base font-semibold text-slate-100">{title}</h2>
      )}
      {subtitle && <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>}
      <div className={title || subtitle ? "mt-4" : ""}>{children}</div>
    </section>
  );
}
