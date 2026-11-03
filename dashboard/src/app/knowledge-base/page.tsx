"use client";

import * as React from "react";
import {
  api,
  KnowledgeBaseItem,
  KnowledgeBaseResponse,
} from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  BookOpen,
  Search,
  Plus,
  Edit2,
  Trash2,
  RefreshCw,
  Folder,
  FileText,
  Clock,
  Check,
  AlertCircle,
} from "lucide-react";

export default function KnowledgeBasePage() {
  const [data, setData] = React.useState<KnowledgeBaseResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [activeSection, setActiveSection] = React.useState<string>("all");
  const [search, setSearch] = React.useState("");

  // Editor Modal State (for both create and edit)
  const [editorOpen, setEditorOpen] = React.useState(false);
  const [editingItem, setEditingItem] = React.useState<KnowledgeBaseItem | null>(null);
  const [formSection, setFormSection] = React.useState("");
  const [formTitle, setFormTitle] = React.useState("");
  const [formContent, setFormContent] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);

  // Delete Confirmation State
  const [deletingId, setDeletingId] = React.useState<number | null>(null);

  const fetchKnowledgeBase = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getKnowledgeBase({
        section: activeSection,
        search: search.trim() || undefined,
      });
      setData(res);
    } catch (err) {
      console.error("Failed to load knowledge base", err);
    } finally {
      setLoading(false);
    }
  }, [activeSection, search]);

  React.useEffect(() => {
    fetchKnowledgeBase();
  }, [fetchKnowledgeBase]);

  const handleOpenCreate = () => {
    setEditingItem(null);
    setFormSection(activeSection !== "all" ? activeSection : "shipping");
    setFormTitle("");
    setFormContent("");
    setErrorMsg(null);
    setEditorOpen(true);
  };

  const handleOpenEdit = (item: KnowledgeBaseItem) => {
    setEditingItem(item);
    setFormSection(item.section);
    setFormTitle(item.title);
    setFormContent(item.content);
    setErrorMsg(null);
    setEditorOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formSection.trim() || !formTitle.trim() || !formContent.trim()) {
      setErrorMsg("Please fill out all fields.");
      return;
    }

    setSaving(true);
    setErrorMsg(null);

    try {
      if (editingItem) {
        await api.updateKnowledgeBase(editingItem.id, {
          section: formSection.trim(),
          title: formTitle.trim(),
          content: formContent.trim(),
        });
      } else {
        await api.saveKnowledgeBase({
          section: formSection.trim(),
          title: formTitle.trim(),
          content: formContent.trim(),
        });
      }
      setEditorOpen(false);
      fetchKnowledgeBase();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to save knowledge base entry.");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this knowledge base entry?")) {
      return;
    }
    setDeletingId(id);
    try {
      await api.deleteKnowledgeBase(id);
      fetchKnowledgeBase();
    } catch (err) {
      console.error("Failed to delete entry", err);
    } finally {
      setDeletingId(null);
    }
  };

  const sections = data?.sections || [];
  const items = data?.items || [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      {/* Top Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-neutral-900 flex items-center space-x-2">
            <BookOpen className="h-5 w-5" />
            <span>Knowledge Base</span>
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Grounded documentation, company policies, and FAQs that guide the AI support agent responses.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchKnowledgeBase}
            disabled={loading}
            className="h-8 text-xs font-medium"
          >
            <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          <Button
            size="sm"
            onClick={handleOpenCreate}
            className="h-8 text-xs font-medium bg-black text-white hover:bg-neutral-800"
          >
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            Add Entry
          </Button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setActiveSection("all")}
            className={`rounded-md px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
              activeSection === "all"
                ? "bg-black text-white"
                : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 hover:text-black"
            }`}
          >
            All Sections
          </button>
          {sections.map((sec) => (
            <button
              key={sec}
              onClick={() => setActiveSection(sec)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                activeSection === sec
                  ? "bg-black text-white"
                  : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 hover:text-black"
              }`}
            >
              {sec}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-80">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-neutral-400" />
          <Input
            placeholder="Search articles, policies, headings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 pl-8 text-xs"
          />
        </div>
      </div>

      {/* Content Grid */}
      {loading && items.length === 0 ? (
        <div className="flex h-48 items-center justify-center">
          <div className="flex items-center space-x-2 text-xs text-neutral-500">
            <div className="h-4 w-4 animate-spin rounded-full border border-black border-t-transparent" />
            <span>Loading knowledge base...</span>
          </div>
        </div>
      ) : items.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => (
            <Card
              key={item.id}
              className="border-neutral-200 hover:border-neutral-300 transition-colors flex flex-col justify-between"
            >
              <CardHeader className="p-4 pb-2">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="inline-flex items-center space-x-1 rounded bg-neutral-100 px-2 py-0.5 text-[11px] font-mono uppercase text-neutral-700">
                    <Folder className="h-3 w-3" />
                    <span>{item.section}</span>
                  </span>
                  <span className="text-[11px] font-mono text-neutral-400 flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>{formatDate(item.updated_at)}</span>
                  </span>
                </div>
                <CardTitle className="text-sm font-semibold line-clamp-1 text-neutral-900">
                  {item.title}
                </CardTitle>
              </CardHeader>

              <CardContent className="p-4 pt-1 flex-1">
                <p className="text-xs text-neutral-600 line-clamp-4 whitespace-pre-wrap leading-relaxed font-sans">
                  {item.content}
                </p>
              </CardContent>

              <CardFooter className="p-4 pt-2 border-t border-neutral-100 flex items-center justify-between bg-neutral-50/50">
                <span className="font-mono text-[11px] text-neutral-400">ID #{item.id}</span>
                <div className="flex items-center space-x-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleOpenEdit(item)}
                    className="h-7 px-2 text-xs hover:bg-neutral-200"
                  >
                    <Edit2 className="h-3 w-3 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={deletingId === item.id}
                    onClick={() => handleDelete(item.id)}
                    className="h-7 px-2 text-xs text-neutral-600 hover:text-black hover:bg-neutral-200"
                  >
                    <Trash2 className="h-3 w-3 mr-1" />
                    Delete
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="border-neutral-200 p-12 text-center">
          <BookOpen className="mx-auto h-8 w-8 text-neutral-400 mb-2" />
          <h3 className="text-sm font-semibold text-neutral-900">No entries found</h3>
          <p className="text-xs text-neutral-500 mt-1 max-w-sm mx-auto">
            No knowledge base entries matched your filter. You can add new policies or seed the knowledge base.
          </p>
          <div className="mt-4">
            <Button size="sm" onClick={handleOpenCreate} className="h-8 text-xs bg-black text-white">
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              Create First Entry
            </Button>
          </div>
        </Card>
      )}

      {/* Create / Edit Dialog */}
      <Dialog open={editorOpen} onOpenChange={setEditorOpen}>
        <form onSubmit={handleSave}>
          <DialogHeader onClose={() => setEditorOpen(false)}>
            <DialogTitle>
              {editingItem ? `Edit Entry #${editingItem.id}` : "Create Knowledge Base Entry"}
            </DialogTitle>
            <DialogDescription>
              This content will be made available to the AI support model for retrieval.
            </DialogDescription>
          </DialogHeader>

          <DialogContent className="space-y-4">
            {errorMsg && (
              <div className="flex items-center space-x-2 rounded-md border border-neutral-300 bg-neutral-100 p-2.5 text-xs text-neutral-900">
                <AlertCircle className="h-4 w-4 shrink-0 text-neutral-800" />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-medium text-neutral-700">Section Name</label>
              <Input
                placeholder="e.g. shipping, returns, warranty"
                value={formSection}
                onChange={(e) => setFormSection(e.target.value)}
                required
                className="h-8 text-xs font-mono"
              />
              <p className="text-[11px] text-neutral-400">
                Common sections: shipping, returns, order_status, warranties, products
              </p>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-neutral-700">Title / Topic</label>
              <Input
                placeholder="e.g. Return Window & Eligibility"
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                required
                className="h-8 text-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-neutral-700">Content / Policy Details</label>
              <Textarea
                rows={6}
                placeholder="Write detailed instructions, rules, or answers for the AI agent..."
                value={formContent}
                onChange={(e) => setFormContent(e.target.value)}
                required
                className="text-xs font-mono"
              />
            </div>
          </DialogContent>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setEditorOpen(false)}
              className="h-8 text-xs"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={saving}
              className="h-8 text-xs bg-black text-white hover:bg-neutral-800"
            >
              {saving ? "Saving..." : editingItem ? "Update Entry" : "Save Entry"}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}

