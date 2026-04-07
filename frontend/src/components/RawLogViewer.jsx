import { PanelCard } from './PanelCard';

export function RawLogViewer({ content }) {
  return (
    <PanelCard title="Raw Logs Viewer" subtitle="Original uploaded data" className="h-full">
      <pre className="max-h-[24rem] overflow-auto rounded-lg bg-black/30 p-4 font-mono text-xs leading-5 text-slate-200">
        {content || 'No logs loaded yet.'}
      </pre>
    </PanelCard>
  );
}
