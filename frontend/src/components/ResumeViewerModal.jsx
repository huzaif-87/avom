import React, { useState } from 'react';
import {
  X,
  FileText,
  Download,
  ExternalLink,
  AlertCircle,
  Eye,
  CheckCircle2,
  FileQuestion,
} from 'lucide-react';
import { getResumeViewUrl, getResumeDownloadUrl } from '../services/api';

export default function ResumeViewerModal({ candidate, isOpen, onClose }) {
  const [iframeError, setIframeError] = useState(false);

  if (!isOpen || !candidate) return null;

  const candidateId = candidate.candidate_id;
  const filename = candidate.filename || 'resume';
  const isDocx = filename.toLowerCase().endsWith('.docx');
  const isPdf = filename.toLowerCase().endsWith('.pdf') || !isDocx;
  const viewUrl = getResumeViewUrl(candidateId);
  const downloadUrl = getResumeDownloadUrl(candidateId);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal/60 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl border border-sage-muted w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-sage-muted/60 bg-cream-50/80">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-olive-light border border-sage/60 flex items-center justify-center text-olive-dark shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h3 className="text-base font-bold text-charcoal truncate">
                {candidate.name && candidate.name !== 'Unknown'
                  ? `${candidate.name} — Resume Preview`
                  : `Resume: ${filename}`}
              </h3>
              <p className="text-xs text-charcoal-muted truncate flex items-center gap-2 mt-0.5">
                <span>{filename}</span>
                {candidate.page_count && (
                  <>
                    <span>•</span>
                    <span>{candidate.page_count} page{candidate.page_count > 1 ? 's' : ''}</span>
                  </>
                )}
                {candidate.file_type && (
                  <span className="uppercase text-[10px] font-semibold bg-cream-200 text-charcoal-muted px-1.5 py-0.5 rounded">
                    {candidate.file_type}
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Download Original Button */}
            <a
              href={downloadUrl}
              download={filename}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-charcoal bg-white border border-sage-muted rounded-lg hover:bg-cream-100 hover:text-olive-dark transition shadow-2xs"
              title="Download original uploaded file"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download</span>
            </a>

            {/* Open in new tab (PDFs only) */}
            {isPdf && (
              <a
                href={viewUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-olive hover:bg-olive-dark rounded-lg transition shadow-xs"
                title="Open in browser preview window"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Open in Tab</span>
              </a>
            )}

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-charcoal-muted hover:text-charcoal hover:bg-cream-100 transition"
              title="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body Viewer */}
        <div className="flex-1 min-h-[500px] bg-cream-100 flex flex-col relative overflow-hidden">
          {isPdf ? (
            !iframeError ? (
              <iframe
                src={`${viewUrl}#toolbar=1&navpanes=0`}
                title={`Resume - ${filename}`}
                className="w-full h-full min-h-[550px] border-none"
                onError={() => setIframeError(true)}
              />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-white">
                <FileQuestion className="w-12 h-12 text-terracotta-dark mb-3" />
                <h4 className="text-sm font-semibold text-charcoal">
                  Direct In-Browser Preview Unavailable
                </h4>
                <p className="text-xs text-charcoal-muted max-w-md mt-1 mb-4">
                  Your browser blocked the inline preview of this PDF. You can open it directly in a dedicated tab or download the file.
                </p>
                <div className="flex items-center gap-3">
                  <a
                    href={viewUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-olive rounded-xl hover:bg-olive-dark transition"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>Open in New Tab</span>
                  </a>
                  <a
                    href={downloadUrl}
                    download={filename}
                    className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-charcoal bg-white border border-sage-muted rounded-xl hover:bg-cream-100 transition"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download File</span>
                  </a>
                </div>
              </div>
            )
          ) : (
            /* Word Document (.docx) Fallback Presentation */
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-white">
              <div className="w-16 h-16 rounded-2xl bg-olive-light border border-sage/60 flex items-center justify-center text-olive-dark mb-4 shadow-xs">
                <FileText className="w-8 h-8" />
              </div>
              <h4 className="text-base font-bold text-charcoal">
                Microsoft Word Document ({filename})
              </h4>
              <p className="text-xs text-charcoal-muted max-w-md mt-2 mb-5 leading-relaxed">
                DOCX documents cannot be rendered directly inside an embedded web viewer. All candidate text and skills were successfully extracted into your analysis. You can download the original file to view its exact styling in Microsoft Word or LibreOffice.
              </p>

              <div className="flex items-center gap-3">
                <a
                  href={downloadUrl}
                  download={filename}
                  className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-olive rounded-xl hover:bg-olive-dark transition shadow-xs"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Original DOCX</span>
                </a>
              </div>

              {/* Extracted text snippet */}
              {candidate.raw_text && (
                <div className="w-full max-w-2xl mt-8 text-left border border-sage-muted rounded-xl p-4 bg-cream-50">
                  <div className="text-[11px] font-semibold text-charcoal-muted uppercase tracking-wider mb-2">
                    Extracted Text Preview:
                  </div>
                  <div className="max-h-48 overflow-y-auto text-xs text-charcoal font-mono whitespace-pre-wrap leading-relaxed">
                    {candidate.raw_text.slice(0, 1500)}
                    {candidate.raw_text.length > 1500 && '...'}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer info bar */}
        <div className="px-6 py-2.5 bg-cream-50/90 border-t border-sage-muted/60 text-[11px] text-charcoal-muted flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-olive" />
            <span>Retrieved securely from in-memory session cache</span>
          </div>
          <span className="text-charcoal-muted/70">Candidate ID: {candidateId}</span>
        </div>
      </div>
    </div>
  );
}
