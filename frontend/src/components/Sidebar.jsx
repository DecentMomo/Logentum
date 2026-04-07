import { Bot, ChartPie, FileCog, Radar, Search } from 'lucide-react';

const navItems = [
  { label: 'Parser', icon: FileCog, active: true },
  { label: 'Semantic Search', icon: Search, active: false },
  { label: 'Anomaly Detection', icon: Radar, active: false },
  { label: 'Summarization', icon: Bot, active: false },
  { label: 'Dashboard', icon: ChartPie, active: false }
];

export function Sidebar() {
  return (
    <aside className="w-full border-b border-slate-800 bg-steel/80 px-4 py-4 md:w-72 md:border-b-0 md:border-r md:px-5 md:py-6">
      <div className="mb-6">
        <p className="font-heading text-xs uppercase tracking-[0.2em] text-slate-400">Modules</p>
      </div>
      <nav className="space-y-2">
        {navItems.map(({ label, icon: Icon, active }) => (
          <button
            key={label}
            type="button"
            disabled={!active}
            className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left transition ${
              active
                ? 'border-accent/50 bg-accent/10 text-accent'
                : 'cursor-not-allowed border-slate-700/50 bg-slate-900/40 text-slate-400'
            }`}
          >
            <span className="flex items-center gap-2 text-sm">
              <Icon className="h-4 w-4" />
              {label}
            </span>
            {!active ? (
              <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[10px] uppercase tracking-[0.08em]">
                Soon
              </span>
            ) : null}
          </button>
        ))}
      </nav>
    </aside>
  );
}
