"use client";

import * as React from "react";
import { api, EventItem, EventsResponse } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Activity,
  CheckCircle2,
  Clock,
  AlertOctagon,
  MinusCircle,
  RefreshCw,
  Search,
  Eye,
  Copy,
  Check,
} from "lucide-react";

export default function EventsPage() {
  const [data, setData] = React.useState<EventsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [statusFilter, setStatusFilter] = React.useState<string>("all");
  const [search, setSearch] = React.useState("");
  const [selectedEvent, setSelectedEvent] = React.useState<EventItem | null>(null);
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const fetchEvents = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getEvents({
        status: statusFilter,
        search: search.trim() || undefined,
        limit: 100,
      });
      setData(res);
    } catch (err) {
      console.error("Failed to load events", err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, search]);

  React.useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(text);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusBadge = (status: EventItem["status"]) => {
    switch (status) {
      case "processed":
        return (
          <Badge variant="default" className="flex items-center space-x-1 bg-[#111111] text-white border-[#111111]">
            <CheckCircle2 className="h-3 w-3" />
            <span>processed</span>
          </Badge>
        );
      case "processing":
        return (
          <Badge variant="outline" className="flex items-center space-x-1 border-[#D1D5DB] bg-[#F5F5F5] text-[#111111]">
            <Clock className="h-3 w-3 animate-spin" />
            <span>processing</span>
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="flex items-center space-x-1 bg-[#222222] border-[#333333] text-white">
            <AlertOctagon className="h-3 w-3" />
            <span>failed</span>
          </Badge>
        );
      case "skipped":
        return (
          <Badge variant="secondary" className="flex items-center space-x-1 bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]">
            <MinusCircle className="h-3 w-3" />
            <span>skipped</span>
          </Badge>
        );
      default:
        return <Badge variant="outline" className="border-[#E5E7EB] text-[#333333]">{status}</Badge>;
    }
  };

  const stats = data?.stats || {
    total: 0,
    processed: 0,
    processing: 0,
    skipped: 0,
    failed: 0,
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      {/* Top Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[#111111] flex items-center space-x-2">
            <Activity className="h-5 w-5 text-[#111111]" />
            <span>Pipeline Events</span>
          </h1>
          <p className="text-xs text-[#6B7280] mt-1">
            Real-time audit log of incoming emails, pipeline execution, and AI decisions.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchEvents}
            disabled={loading}
            className="h-8 text-xs font-medium border-[#E5E7EB] bg-white text-[#111111] hover:bg-[#F5F5F5] hover:border-[#D1D5DB]"
          >
            <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5 mb-6">
        <Card className="border-[#E5E7EB] bg-white">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
              Total Events
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-[#111111]">{stats.total}</div>
          </CardContent>
        </Card>

        <Card className="border-[#E5E7EB] bg-white">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
              Processed
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-[#111111]">{stats.processed}</div>
          </CardContent>
        </Card>

        <Card className="border-[#E5E7EB] bg-white">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
              Processing
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-[#111111]">{stats.processing}</div>
          </CardContent>
        </Card>

        <Card className="border-[#E5E7EB] bg-white">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
              Skipped
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-[#6B7280]">{stats.skipped}</div>
          </CardContent>
        </Card>

        <Card className="border-[#E5E7EB] bg-white">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
              Failed
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-[#111111]">{stats.failed}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          {(["all", "processed", "processing", "skipped", "failed"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                statusFilter === s
                  ? "bg-[#111111] text-white border border-[#111111]"
                  : "bg-[#F5F5F5] text-[#6B7280] border border-[#E5E7EB] hover:bg-[#E5E7EB] hover:text-[#111111]"
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#9CA3AF]" />
          <Input
            placeholder="Search message ID, errors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 pl-8 text-xs border-[#E5E7EB] bg-white text-[#111111] placeholder:text-[#9CA3AF] focus-visible:border-[#111111]"
          />
        </div>
      </div>

      {/* Events Table */}
      <Card className="border-[#E5E7EB] bg-white overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-[#F5F5F5]/80 border-b border-[#E5E7EB]">
              <TableHead className="w-16 text-[#6B7280]">ID</TableHead>
              <TableHead className="text-[#6B7280]">Status</TableHead>
              <TableHead className="text-[#6B7280]">Gmail Message ID</TableHead>
              <TableHead className="text-[#6B7280]">Attempts</TableHead>
              <TableHead className="text-[#6B7280]">Result Summary</TableHead>
              <TableHead className="text-[#6B7280]">Created At</TableHead>
              <TableHead className="text-right text-[#6B7280]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (!data || data.items.length === 0) ? (
              <TableRow>
                <TableCell colSpan={7} className="h-32 text-center text-xs text-[#6B7280]">
                  <div className="flex items-center justify-center space-x-2">
                    <div className="h-4 w-4 animate-spin rounded-full border border-[#111111] border-t-transparent" />
                    <span>Loading events...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : data && data.items.length > 0 ? (
              data.items.map((event) => {
                const actionResult = event.result as Record<string, unknown> | null;
                const decision = (actionResult?.decision as Record<string, unknown>) || null;
                const actionType = decision?.action || actionResult?.action || null;

                return (
                  <TableRow key={event.id} className="hover:bg-[#F5F5F5]/60 transition-colors border-b border-[#E5E7EB]">
                    <TableCell className="font-mono text-xs text-[#6B7280]">#{event.id}</TableCell>
                    <TableCell>{getStatusBadge(event.status)}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1.5 font-mono text-xs text-[#333333]">
                        <span className="truncate max-w-[140px] sm:max-w-[200px]" title={event.gmail_message_id}>
                          {event.gmail_message_id}
                        </span>
                        <button
                          onClick={() => copyToClipboard(event.gmail_message_id)}
                          className="text-[#6B7280] hover:text-[#111111] transition-colors"
                        >
                          {copiedId === event.gmail_message_id ? (
                            <Check className="h-3 w-3 text-[#111111]" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </button>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-[#333333]">{event.attempts}</TableCell>
                    <TableCell>
                      {event.error ? (
                        <span className="truncate max-w-[220px] inline-block text-xs text-[#111111] font-mono bg-[#F5F5F5] border border-[#E5E7EB] px-1.5 py-0.5 rounded">
                          {event.error}
                        </span>
                      ) : actionType ? (
                        <span className="inline-flex items-center rounded border border-[#E5E7EB] px-2 py-0.5 text-xs font-medium uppercase text-[#333333] bg-[#F5F5F5]">
                          {String(actionType)}
                        </span>
                      ) : event.result ? (
                        <span className="text-xs text-[#6B7280] font-mono">Payload stored</span>
                      ) : (
                        <span className="text-xs text-[#9CA3AF]">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-[#6B7280] font-mono">
                      {formatDate(event.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedEvent(event)}
                        className="h-7 px-2 text-xs border-[#E5E7EB] bg-white text-[#111111] hover:bg-[#F5F5F5]"
                      >
                        <Eye className="mr-1 h-3 w-3" />
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="h-32 text-center text-xs text-[#6B7280]">
                  No events found matching your filter criteria.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Details Dialog Modal */}
      <Dialog open={!!selectedEvent} onOpenChange={(open) => !open && setSelectedEvent(null)}>
        {selectedEvent && (
          <>
            <DialogHeader onClose={() => setSelectedEvent(null)}>
              <DialogTitle>Event Details #{selectedEvent.id}</DialogTitle>
              <DialogDescription>
                Gmail Message ID: <span className="font-mono text-[#111111]">{selectedEvent.gmail_message_id}</span>
              </DialogDescription>
            </DialogHeader>

            <DialogContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 border-b border-[#E5E7EB] pb-4 text-xs">
                <div>
                  <span className="text-[#6B7280]">Status</span>
                  <div className="mt-1">{getStatusBadge(selectedEvent.status)}</div>
                </div>
                <div>
                  <span className="text-[#6B7280]">Attempts</span>
                  <div className="mt-1 font-mono font-medium text-[#111111]">{selectedEvent.attempts}</div>
                </div>
                <div>
                  <span className="text-[#6B7280]">Created At</span>
                  <div className="mt-1 font-mono text-[#333333]">{formatDate(selectedEvent.created_at)}</div>
                </div>
                <div>
                  <span className="text-[#6B7280]">Processed At</span>
                  <div className="mt-1 font-mono text-[#333333]">{formatDate(selectedEvent.processed_at)}</div>
                </div>
              </div>

              {selectedEvent.error && (
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-[#111111]">Error Log</span>
                  <pre className="rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3 text-xs font-mono text-[#111111] whitespace-pre-wrap">
                    {selectedEvent.error}
                  </pre>
                </div>
              )}

              <div className="space-y-1">
                <span className="text-xs font-semibold text-[#111111]">Execution Result (JSON)</span>
                <pre className="max-h-72 overflow-auto rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3 text-xs font-mono text-[#111111]">
                  {selectedEvent.result
                    ? JSON.stringify(selectedEvent.result, null, 2)
                    : "No result payload recorded."}
                </pre>
              </div>
            </DialogContent>

            <DialogFooter>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedEvent(null)}
                className="h-8 text-xs border-[#E5E7EB] text-[#111111] hover:bg-[#F5F5F5]"
              >
                Close
              </Button>
            </DialogFooter>
          </>
        )}
      </Dialog>
    </div>
  );
}
