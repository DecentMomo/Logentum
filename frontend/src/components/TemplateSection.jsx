import { Layers } from 'lucide-react';
import { PanelCard } from './PanelCard';

export function TemplateSection({ templates }) {
  const entries = Object.entries(templates);

  return (
    <PanelCard
      title="Template View"
      subtitle="Extracted templates grouped by template_id"
      action={
        <span className="inline-flex items-center gap-1 rounded-full border border-slate-600 bg-slate-900/50 px-2 py-1 text-[11px] text-slate-300">
          <Layers className="h-3.5 w-3.5" />
          {entries.length} templates
        </span>
      }
    >
      {entries.length === 0 ? (
        <p className="text-sm text-slate-400">No templates generated yet. Parse a file to view grouped patterns.</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {entries.map(([templateId, item]) => (
            <article key={templateId} className="rounded-lg border border-slate-700 bg-slate-900/40 p-4">
              <p className="font-mono text-xs text-cyan-300">{templateId}</p>
              <p className="mt-2 text-sm text-slate-200">{item.template}</p>
              <p className="mt-3 text-xs text-slate-400">{item.count} log lines</p>
            </article>
          ))}
        </div>
      )}
    </PanelCard>
  );
}
