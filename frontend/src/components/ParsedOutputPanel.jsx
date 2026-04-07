import { PanelCard } from './PanelCard';

export function ParsedOutputPanel({ parsedLogs }) {
  return (
    <PanelCard title="Parsed Output" subtitle="Structured JSON result" className="h-full">
      <pre className="max-h-[24rem] overflow-auto rounded-lg bg-black/30 p-4 font-mono text-xs leading-5 text-cyan-100">
        {parsedLogs.length ? JSON.stringify(parsedLogs, null, 2) : '[ ]'}
      </pre>
    </PanelCard>
  );
}
