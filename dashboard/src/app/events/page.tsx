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
          <Badge variant="default" className="flex items-center space-x-1 bg-black text-white">
            <CheckCircle2 className="h-3 w-3" />
            <span>processed</span>
          </Badge>
        );
      case "processing":
        return (
          <Badge variant="outline" className="flex items-center space-x-1 border-neutral-400 text-neutral-900">
            <Clock className="h-3 w-3 animate-spin" />
            <span>processing</span>
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="flex items-center space-x-1 bg-neutral-900 text-white">
            <AlertOctagon className="h-3 w-3" />
            <span>failed</span>
          </Badge>
        );
      case "skipped":
        return (
          <Badge variant="secondary" className="flex items-center space-x-1 bg-neutral-100 text-neutral-600">
            <MinusCircle className="h-3 w-3" />
            <span>skipped</span>
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
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
          <h1 className="text-xl font-bold tracking-tight text-neutral-900 flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Pipeline Events</span>
          </h1>
          <p className="text-xs text-neutral-500 mt-1">
            Real-time audit log of incoming emails, pipeline execution, and AI decisions.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchEvents}
            disabled={loading}
            className="h-8 text-xs font-medium"
          >
            <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5 mb-6">
        <Card className="border-neutral-200">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-neutral-500">
              Total Events
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight">{stats.total}</div>
          </CardContent>
        </Card>

        <Card className="border-neutral-200">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-neutral-500">
              Processed
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-neutral-900">{stats.processed}</div>
          </CardContent>
        </Card>

        <Card className="border-neutral-200">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-neutral-500">
              Processing
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-neutral-900">{stats.processing}</div>
          </CardContent>
        </Card>

        <Card className="border-neutral-200">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-neutral-500">
              Skipped
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-neutral-500">{stats.skipped}</div>
          </CardContent>
        </Card>

        <Card className="border-neutral-200">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-neutral-500">
              Failed
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-neutral-900">{stats.failed}</div>
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
                  ? "bg-black text-white"
                  : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200 hover:text-black"
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-neutral-400" />
          <Input
            placeholder="Search message ID, errors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 pl-8 text-xs"
          />
        </div>
      </div>

      {/* Events Table */}
      <Card className="border-neutral-200 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-neutral-50/50">
              <TableHead className="w-16">ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Gmail Message ID</TableHead>
              <TableHead>Attempts</TableHead>
              <TableHead>Result Summary</TableHead>
              <TableHead>Created At</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (!data || data.items.length === 0) ? (
              <TableRow>
                <TableCell colSpan={7} className="h-32 text-center text-xs text-neutral-500">
                  <div className="flex items-center justify-center space-x-2">
                    <div className="h-4 w-4 animate-spin rounded-full border border-black border-t-transparent" />
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
                  <TableRow key={event.id} className="hover:bg-neutral-50/50 transition-colors">
                    <TableCell className="font-mono text-xs text-neutral-500">#{event.id}</TableCell>
                    <TableCell>{getStatusBadge(event.status)}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1.5 font-mono text-xs text-neutral-800">
                        <span className="truncate max-w-[140px] sm:max-w-[200px]" title={event.gmail_message_id}>
                          {event.gmail_message_id}
                        </span>
                        <button
                          onClick={() => copyToClipboard(event.gmail_message_id)}
                          className="text-neutral-400 hover:text-black transition-colors"
                        >
                          {copiedId === event.gmail_message_id ? (
                            <Check className="h-3 w-3 text-black" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </button>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs">{event.attempts}</TableCell>
                    <TableCell>
                      {event.error ? (
                        <span className="truncate max-w-[220px] inline-block text-xs text-neutral-800 font-mono bg-neutral-100 px-1.5 py-0.5 rounded">
                          {event.error}
                        </span>
                      ) : actionType ? (
                        <span className="inline-flex items-center rounded border border-neutral-200 px-2 py-0.5 text-xs font-medium uppercase text-neutral-800 bg-neutral-50">
                          {String(actionType)}
                        </span>
                      ) : event.result ? (
                        <span className="text-xs text-neutral-500 font-mono">Payload stored</span>
                      ) : (
                        <span className="text-xs text-neutral-400">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-neutral-500 font-mono">
                      {formatDate(event.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedEvent(event)}
                        className="h-7 px-2 text-xs hover:bg-neutral-100"
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
                <TableCell colSpan={7} className="h-32 text-center text-xs text-neutral-500">
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
                Gmail Message ID: <span className="font-mono text-black">{selectedEvent.gmail_message_id}</span>
              </DialogDescription>
            </DialogHeader>

            <DialogContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 border-b border-neutral-100 pb-4 text-xs">
                <div>
                  <span className="text-neutral-500">Status</span>
                  <div className="mt-1">{getStatusBadge(selectedEvent.status)}</div>
                </div>
                <div>
                  <span className="text-neutral-500">Attempts</span>
                  <div className="mt-1 font-mono font-medium">{selectedEvent.attempts}</div>
                </div>
                <div>
                  <span className="text-neutral-500">Created At</span>
                  <div className="mt-1 font-mono text-neutral-700">{formatDate(selectedEvent.created_at)}</div>
                </div>
                <div>
                  <span className="text-neutral-500">Processed At</span>
                  <div className="mt-1 font-mono text-neutral-700">{formatDate(selectedEvent.processed_at)}</div>
                </div>
              </div>

              {selectedEvent.error && (
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-black">Error Log</span>
                  <pre className="rounded-md border border-neutral-300 bg-neutral-100 p-3 text-xs font-mono text-neutral-900 whitespace-pre-wrap">
                    {selectedEvent.error}
                  </pre>
                </div>
              )}

              <div className="space-y-1">
                <span className="text-xs font-semibold text-black">Execution Result (JSON)</span>
                <pre className="max-h-72 overflow-auto rounded-md border border-neutral-200 bg-neutral-50 p-3 text-xs font-mono text-neutral-900">
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
                className="h-8 text-xs"
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

