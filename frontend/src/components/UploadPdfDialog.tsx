"use client";

import * as React from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { FileUp, FileText, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

interface UploadPdfDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sections: string[];
  activeSection: string;
  onSuccess: () => void;
}

export function UploadPdfDialog({
  open,
  onOpenChange,
  sections,
  activeSection,
  onSuccess,
}: UploadPdfDialogProps) {
  const [file, setFile] = React.useState<File | null>(null);
  const [section, setSection] = React.useState(activeSection !== "all" ? activeSection : "smartphone");
  const [title, setTitle] = React.useState("");
  const [uploading, setUploading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<{ pages: number; chunks: number; title: string } | null>(null);
  const [dragActive, setDragActive] = React.useState(false);

  React.useEffect(() => {
    if (open) {
      setFile(null);
      setSection(activeSection !== "all" ? activeSection : "smartphone");
      setTitle("");
      setError(null);
      setResult(null);
    }
  }, [open, activeSection]);

  const handleFileChange = (selectedFile: File | null) => {
    if (!selectedFile) return;
    if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a valid PDF file.");
      return;
    }
    setFile(selectedFile);
    setError(null);
    if (!title.trim()) {
      setTitle(selectedFile.name.replace(/\.pdf$/i, ""));
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a PDF file to upload.");
      return;
    }
    if (!section.trim()) {
      setError("Please select a documentation section.");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("section", section.trim());
      if (title.trim()) {
        formData.append("title", title.trim());
      }

      const res = await api.uploadKnowledgeBasePdf(formData);
      setResult({
        pages: res.pages,
        chunks: res.chunks,
        title: res.title,
      });
      setTimeout(() => {
        onSuccess();
        onOpenChange(false);
      }, 1500);
    } catch (err: any) {
      setError(err?.message || "Failed to upload and parse PDF.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileUp className="w-5 h-5 text-blue-600" />
            Upload PDF Document
          </DialogTitle>
          <DialogDescription>
            Upload product user manuals, troubleshooting guides, or policy PDFs. Documents will be parsed, chunked with page metadata, and indexed for hybrid retrieval.
          </DialogDescription>
        </DialogHeader>

        {result ? (
          <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
            <CheckCircle2 className="w-12 h-12 text-emerald-500 animate-in zoom-in-75 duration-300" />
            <h3 className="font-semibold text-lg">Document Indexed Successfully</h3>
            <p className="text-sm text-muted-foreground">
              Parsed <strong>{result.pages} pages</strong> and created <strong>{result.chunks} indexed chunks</strong> for &quot;{result.title}&quot;.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 pt-2">
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-md flex items-center gap-2 text-sm text-red-500">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Drag & Drop Area */}
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                dragActive ? "border-blue-500 bg-blue-50/10" : "border-border hover:border-blue-400"
              } ${file ? "bg-muted/40" : ""}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById("pdf-file-input")?.click()}
            >
              <input
                id="pdf-file-input"
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
                disabled={uploading}
              />
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <FileText className="w-8 h-8 text-blue-600 shrink-0" />
                  <div className="text-left overflow-hidden">
                    <p className="font-medium text-sm truncate max-w-[240px]">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB • PDF
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-1">
                  <FileUp className="w-8 h-8 text-muted-foreground mx-auto" />
                  <p className="text-sm font-medium">Click to upload or drag & drop</p>
                  <p className="text-xs text-muted-foreground">PDF documents up to 15MB</p>
                </div>
              )}
            </div>

            {/* Section Selection */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Section</label>
              <select
                className="w-full h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={section}
                onChange={(e) => setSection(e.target.value)}
                disabled={uploading}
              >
                {sections.length > 0 ? (
                  sections.map((s) => (
                    <option key={s} value={s} className="bg-popover text-popover-foreground">
                      {s}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="smartphone">smartphone</option>
                    <option value="accessories">accessories</option>
                    <option value="returns-and-warranty">returns-and-warranty</option>
                    <option value="shipping">shipping</option>
                    <option value="other">other</option>
                  </>
                )}
              </select>
            </div>

            {/* Title Input */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Title</label>
              <Input
                placeholder="e.g. Nexa One Pro User Manual"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={uploading}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={uploading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={!file || uploading}>
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Extracting & Indexing...
                  </>
                ) : (
                  "Upload & Index PDF"
                )}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

