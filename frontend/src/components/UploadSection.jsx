import { useMemo } from 'react';
import { FileText } from 'lucide-react';
import { PanelCard } from './PanelCard';

export function UploadSection({ selectedFile, onFileChange, fileInputRef, onDropFile }) {
  const fileDetails = useMemo(() => {
    if (!selectedFile) {
      return 'Supports .log and .txt files';
    }
    const sizeInKb = (selectedFile.size / 1024).toFixed(1);
    return `${selectedFile.name} (${sizeInKb} KB)`;
  }, [selectedFile]);

  return (
    <PanelCard
      title="File Upload"
      subtitle="Upload raw logs for template extraction and structured parsing"
      className="animate-fade-in"
    >
      <div
        onDragOver={(event) => event.preventDefault()}
        onDrop={onDropFile}
        className="rounded-xl border border-dashed border-slate-600 bg-slate-900/50 p-5 text-center transition hover:border-cyan-400/60"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".log,.txt,text/plain"
          className="hidden"
          onChange={onFileChange}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="inline-flex items-center gap-2 rounded-md border border-slate-600 bg-slate-800 px-4 py-2 text-sm text-slate-200 hover:border-cyan-400/50"
        >
          <FileText className="h-4 w-4" />
          Select Log File
        </button>
        <p className="mt-3 font-mono text-xs text-slate-400">or drag and drop logs here</p>
        <p className="mt-2 text-sm text-slate-300">{fileDetails}</p>
      </div>
    </PanelCard>
  );
}
