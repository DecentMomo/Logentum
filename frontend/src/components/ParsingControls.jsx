import { Play } from 'lucide-react';
import { PanelCard } from './PanelCard';

export function ParsingControls({ onParse, disabled, isParsing }) {
  return (
    <PanelCard title="Parsing Controls" subtitle="Hybrid parser is active (Drain + LLM fallback)">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <p className="text-xs uppercase tracking-[0.08em] text-slate-400">
          Preprocessing + Drain matching + batched LLM fallback
        </p>

        <button
          type="button"
          onClick={onParse}
          disabled={disabled || isParsing}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-teal-400/40 bg-teal-500/10 px-4 py-2 text-sm font-semibold text-teal-200 transition hover:bg-teal-500/20 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Play className="h-4 w-4" />
          {isParsing ? 'Parsing...' : 'Parse Logs'}
        </button>
      </div>
    </PanelCard>
  );
}
