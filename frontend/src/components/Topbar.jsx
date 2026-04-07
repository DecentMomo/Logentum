import { CircleCheck, UploadCloud } from 'lucide-react';

export function Topbar({ onUploadClick, statusText = 'Parser Ready' }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 px-4 py-4 sm:px-6">
      <div>
        <h1 className="font-heading text-xl text-slate-100">Logentum</h1>
        <p className="text-xs text-slate-400">Semantic Log Analysis and Generative Incident Intelligence</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
          <CircleCheck className="h-3.5 w-3.5" />
          {statusText}
        </span>
        <button
          type="button"
          onClick={onUploadClick}
          className="inline-flex items-center gap-2 rounded-lg border border-cyan-400/40 bg-cyan-500/10 px-3 py-2 text-sm font-medium text-cyan-200 transition hover:bg-cyan-500/20"
        >
          <UploadCloud className="h-4 w-4" />
          Upload Log
        </button>
      </div>
    </header>
  );
}
