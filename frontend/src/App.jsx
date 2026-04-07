import { useRef, useState } from 'react';
import { ParsedOutputPanel } from './components/ParsedOutputPanel';
import { ParsingControls } from './components/ParsingControls';
import { RawLogViewer } from './components/RawLogViewer';
import { Sidebar } from './components/Sidebar';
import { TemplateSection } from './components/TemplateSection';
import { Topbar } from './components/Topbar';
import { UploadSection } from './components/UploadSection';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function App() {
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadId, setUploadId] = useState('');
  const [rawContent, setRawContent] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isParsing, setIsParsing] = useState(false);
  const [parsedLogs, setParsedLogs] = useState([]);
  const [templates, setTemplates] = useState({});

  const handleFilePicked = async (file) => {
    if (!file) {
      return;
    }

    setSelectedFile(file);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      });

      if (!uploadResponse.ok) {
        throw new Error('Upload failed');
      }

      const uploadData = await uploadResponse.json();
      setUploadId(uploadData.upload_id);
      setRawContent(uploadData.raw_logs || '');
      setParsedLogs([]);
      setTemplates({});
    } catch (error) {
      console.error(error);
      window.alert('Failed to upload file. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const onFileChange = (event) => {
    const file = event.target.files?.[0];
    handleFilePicked(file);
  };

  const onDropFile = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    handleFilePicked(file);
  };

  const onParse = async () => {
    if (!uploadId) {
      window.alert('Upload a log file before parsing.');
      return;
    }

    setIsParsing(true);

    try {
      const response = await fetch(`${API_BASE}/parse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          upload_id: uploadId,
          parsing_method: 'Hybrid'
        })
      });

      if (!response.ok) {
        throw new Error('Parse failed');
      }

      const result = await response.json();
      setParsedLogs(result.parsed_logs || []);
      setTemplates(result.templates || {});
    } catch (error) {
      console.error(error);
      window.alert('Failed to parse logs. Check backend service and retry.');
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 bg-grid bg-[size:22px_22px]">
      <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,_rgba(34,211,238,0.08),_transparent_35%)]">
        <div className="flex min-h-screen flex-col md:flex-row">
          <Sidebar />

          <main className="flex-1">
            <Topbar onUploadClick={() => fileInputRef.current?.click()} statusText={isUploading ? 'Uploading...' : 'Parser Ready'} />

            <div className="space-y-5 p-4 sm:p-6">
              <UploadSection
                selectedFile={selectedFile}
                onFileChange={onFileChange}
                fileInputRef={fileInputRef}
                onDropFile={onDropFile}
              />

              <ParsingControls
                onParse={onParse}
                disabled={!uploadId}
                isParsing={isParsing}
              />

              <section className="grid gap-5 lg:grid-cols-2">
                <RawLogViewer content={rawContent} />
                <ParsedOutputPanel parsedLogs={parsedLogs} />
              </section>

              <TemplateSection templates={templates} />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;
