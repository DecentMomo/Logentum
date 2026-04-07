export function PanelCard({ title, subtitle, action, children, className = '' }) {
  return (
    <section className={`panel-shell rounded-xl shadow-panel ${className}`}>
      <header className="border-b border-slate-700/50 px-4 py-3 sm:px-5 sm:py-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-heading text-sm uppercase tracking-[0.12em] text-slate-200">{title}</h3>
            {subtitle ? <p className="mt-1 text-xs text-slate-400">{subtitle}</p> : null}
          </div>
          {action}
        </div>
      </header>
      <div className="p-4 sm:p-5">{children}</div>
    </section>
  );
}
