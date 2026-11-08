"use client";

import * as React from "react";
import {
  api,
  TicketItem,
  TicketsResponse,
  TicketDetailResponse,
} from "@/lib/api";
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
  Ticket,
  Search,
  RefreshCw,
  ArrowUpRight,
  MessageSquare,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  User,
  Bot,
} from "lucide-react";

export default function TicketsPage() {
  const [data, setData] = React.useState<TicketsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [statusFilter, setStatusFilter] = React.useState<string>("all");
  const [search, setSearch] = React.useState("");

  // Selected ticket detail state
  const [selectedTicketId, setSelectedTicketId] = React.useState<number | null>(null);
  const [ticketDetail, setTicketDetail] = React.useState<TicketDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = React.useState(false);
  const [updatingStatus, setUpdatingStatus] = React.useState(false);

  const fetchTickets = React.useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getTickets({
        status: statusFilter,
        search: search.trim() || undefined,
        limit: 100,
      });
      setData(res);
    } catch (err) {
      console.error("Failed to load tickets", err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, search]);

  React.useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const loadTicketDetail = async (id: number) => {
    setSelectedTicketId(id);
    setDetailLoading(true);
    try {
      const detail = await api.getTicket(id);
      setTicketDetail(detail);
    } catch (err) {
      console.error("Failed to load ticket detail", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleUpdateStatus = async (
    newStatus: "open" | "answered" | "escalated"
  ) => {
    if (!selectedTicketId || !ticketDetail) return;
    setUpdatingStatus(true);
    try {
      await api.updateTicketStatus(selectedTicketId, { status: newStatus });
      setTicketDetail({
        ...ticketDetail,
        ticket: {
          ...ticketDetail.ticket,
          status: newStatus,
        },
      });
      fetchTickets();
    } catch (err) {
      console.error("Failed to update status", err);
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getStatusBadge = (status: TicketItem["status"]) => {
    switch (status) {
      case "open":
        return (
          <Badge variant="outline" className="flex items-center space-x-1 border-[#D1D5DB] text-[#111111] bg-[#F5F5F5]">
            <HelpCircle className="h-3 w-3" />
            <span>open</span>
          </Badge>
        );
      case "answered":
        return (
          <Badge variant="default" className="flex items-center space-x-1 bg-[#111111] text-white border-[#111111]">
            <CheckCircle className="h-3 w-3" />
            <span>answered</span>
          </Badge>
        );
      case "escalated":
        return (
          <Badge variant="destructive" className="flex items-center space-x-1 bg-[#222222] text-white border-[#333333]">
            <AlertTriangle className="h-3 w-3" />
            <span>escalated</span>
          </Badge>
        );
      default:
        return <Badge variant="outline" className="border-[#E5E7EB] text-[#333333]">{status}</Badge>;
    }
  };

  const stats = data?.stats || {
    total: 0,
    open: 0,
    answered: 0,
    escalated: 0,
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      {/* Top Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[#111111] flex items-center space-x-2">
            <Ticket className="h-5 w-5 text-[#111111]" />
            <span>Customer Tickets</span>
          </h1>
          <p className="text-xs text-[#6B7280] mt-1">
            Manage Gmail support threads, triage categories, AI responses, and human escalations.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchTickets}
            disabled={loading}
            className="h-8 text-xs font-medium border-[#E5E7EB] bg-white text-[#111111] hover:bg-[#F5F5F5] hover:border-[#D1D5DB]"
          >
            <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 mb-6">
        <Card className="border-[#E5E7EB] bg-white">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
              Total Tickets
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-[#111111]">{stats.total}</div>
          </CardContent>
        </Card>

        <Card className="border-[#E5E7EB] bg-white">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
              Open
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-[#111111]">{stats.open}</div>
          </CardContent>
        </Card>

        <Card className="border-[#E5E7EB] bg-white">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
              Answered
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-[#111111]">{stats.answered}</div>
          </CardContent>
        </Card>

        <Card className="border-[#E5E7EB] bg-white">
          <CardHeader className="p-4 pb-1">
            <CardDescription className="text-[11px] font-medium uppercase tracking-wider text-[#6B7280]">
              Escalated
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold tracking-tight text-[#111111]">{stats.escalated}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          {(["all", "open", "answered", "escalated"] as const).map((s) => (
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

        <div className="relative w-full sm:w-80">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#9CA3AF]" />
          <Input
            placeholder="Search customer, subject, category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 pl-8 text-xs border-[#E5E7EB] bg-white text-[#111111] placeholder:text-[#9CA3AF] focus-visible:border-[#111111]"
          />
        </div>
      </div>

      {/* Tickets Table */}
      <Card className="border-[#E5E7EB] bg-white overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-[#F5F5F5]/80 border-b border-[#E5E7EB]">
              <TableHead className="w-16 text-[#6B7280]">ID</TableHead>
              <TableHead className="text-[#6B7280]">Status</TableHead>
              <TableHead className="text-[#6B7280]">Customer / Subject</TableHead>
              <TableHead className="text-[#6B7280]">Category</TableHead>
              <TableHead className="text-[#6B7280]">Proposed Action</TableHead>
              <TableHead className="text-[#6B7280]">Msgs</TableHead>
              <TableHead className="text-[#6B7280]">Updated</TableHead>
              <TableHead className="text-right text-[#6B7280]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (!data || data.items.length === 0) ? (
              <TableRow>
                <TableCell colSpan={8} className="h-32 text-center text-xs text-[#6B7280]">
                  <div className="flex items-center justify-center space-x-2">
                    <div className="h-4 w-4 animate-spin rounded-full border border-[#111111] border-t-transparent" />
                    <span>Loading tickets...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : data && data.items.length > 0 ? (
              data.items.map((ticket) => (
                <TableRow key={ticket.id} className="hover:bg-[#F5F5F5]/60 transition-colors border-b border-[#E5E7EB]">
                  <TableCell className="font-mono text-xs text-[#6B7280]">#{ticket.id}</TableCell>
                  <TableCell>{getStatusBadge(ticket.status)}</TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium text-xs text-[#111111] truncate max-w-[240px]">
                        {ticket.subject || "(No Subject)"}
                      </span>
                      <span className="text-[11px] text-[#6B7280] truncate max-w-[240px]">
                        {ticket.customer_email}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {ticket.category ? (
                      <span className="rounded border border-[#E5E7EB] bg-[#F5F5F5] px-2 py-0.5 text-xs text-[#333333]">
                        {ticket.category}
                      </span>
                    ) : (
                      <span className="text-[#9CA3AF] text-xs">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {ticket.proposed_action ? (
                      <span className="text-xs text-[#333333] truncate max-w-[180px] inline-block font-mono bg-[#F5F5F5] px-1.5 py-0.5 rounded border border-[#E5E7EB]">
                        {ticket.proposed_action}
                      </span>
                    ) : (
                      <span className="text-[#9CA3AF] text-xs">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="inline-flex items-center text-xs text-[#6B7280] font-mono space-x-1">
                      <MessageSquare className="h-3 w-3 text-[#9CA3AF]" />
                      <span>{ticket.message_count ?? 1}</span>
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-[#6B7280] font-mono">
                    {formatDate(ticket.updated_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadTicketDetail(ticket.id)}
                      className="h-7 px-2.5 text-xs border-[#E5E7EB] bg-white text-[#111111] hover:bg-[#F5F5F5]"
                    >
                      <ArrowUpRight className="mr-1 h-3 w-3" />
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={8} className="h-32 text-center text-xs text-[#6B7280]">
                  No tickets found matching your filter criteria.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Ticket Details & Thread Dialog */}
      <Dialog
        open={selectedTicketId !== null}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedTicketId(null);
            setTicketDetail(null);
          }
        }}
      >
        {selectedTicketId !== null && (
          <>
            <DialogHeader onClose={() => setSelectedTicketId(null)}>
              <div className="flex items-center space-x-2">
                <DialogTitle>Ticket #{selectedTicketId}</DialogTitle>
                {ticketDetail && getStatusBadge(ticketDetail.ticket.status)}
              </div>
              <DialogDescription>
                {ticketDetail?.ticket.subject || "Loading thread details..."}
              </DialogDescription>
            </DialogHeader>

            <DialogContent className="space-y-6">
              {detailLoading || !ticketDetail ? (
                <div className="flex h-48 items-center justify-center">
                  <div className="h-5 w-5 animate-spin rounded-full border border-[#111111] border-t-transparent" />
                </div>
              ) : (
                <>
                  {/* Metadata bar */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 rounded-lg border border-[#E5E7EB] bg-[#F5F5F5]/60 p-3 text-xs">
                    <div>
                      <span className="text-[#6B7280]">Customer</span>
                      <div className="font-mono font-medium truncate text-[#111111] mt-0.5">
                        {ticketDetail.ticket.customer_email}
                      </div>
                    </div>
                    <div>
                      <span className="text-[#6B7280]">Category</span>
                      <div className="font-medium text-[#111111] mt-0.5">
                        {ticketDetail.ticket.category || "Unassigned"}
                      </div>
                    </div>
                    <div>
                      <span className="text-[#6B7280]">Proposed Action</span>
                      <div className="font-mono text-[#111111] mt-0.5">
                        {ticketDetail.ticket.proposed_action || "None"}
                      </div>
                    </div>
                    <div>
                      <span className="text-[#6B7280]">Thread ID</span>
                      <div className="font-mono truncate text-[#6B7280] mt-0.5" title={ticketDetail.ticket.gmail_thread_id}>
                        {ticketDetail.ticket.gmail_thread_id}
                      </div>
                    </div>
                  </div>

                  {/* Status Switcher Controls */}
                  <div className="flex items-center justify-between border-b border-[#E5E7EB] pb-3">
                    <span className="text-xs font-semibold text-[#111111]">Change Status</span>
                    <div className="flex items-center space-x-1.5">
                      <Button
                        variant={ticketDetail.ticket.status === "open" ? "default" : "outline"}
                        size="sm"
                        disabled={updatingStatus}
                        onClick={() => handleUpdateStatus("open")}
                        className={`h-7 text-xs px-2.5 ${
                          ticketDetail.ticket.status === "open"
                            ? "bg-[#111111] text-white border-[#111111]"
                            : "bg-white text-[#333333] border-[#E5E7EB] hover:bg-[#F5F5F5]"
                        }`}
                      >
                        Open
                      </Button>
                      <Button
                        variant={ticketDetail.ticket.status === "answered" ? "default" : "outline"}
                        size="sm"
                        disabled={updatingStatus}
                        onClick={() => handleUpdateStatus("answered")}
                        className={`h-7 text-xs px-2.5 ${
                          ticketDetail.ticket.status === "answered"
                            ? "bg-[#111111] text-white border-[#111111]"
                            : "bg-white text-[#333333] border-[#E5E7EB] hover:bg-[#F5F5F5]"
                        }`}
                      >
                        Answered
                      </Button>
                      <Button
                        variant={ticketDetail.ticket.status === "escalated" ? "default" : "outline"}
                        size="sm"
                        disabled={updatingStatus}
                        onClick={() => handleUpdateStatus("escalated")}
                        className={`h-7 text-xs px-2.5 ${
                          ticketDetail.ticket.status === "escalated"
                            ? "bg-[#111111] text-white border-[#111111]"
                            : "bg-white text-[#333333] border-[#E5E7EB] hover:bg-[#F5F5F5]"
                        }`}
                      >
                        Escalated
                      </Button>
                    </div>
                  </div>

                  {/* Conversation Messages Thread */}
                  <div className="space-y-4">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] flex items-center space-x-1.5">
                      <MessageSquare className="h-3.5 w-3.5 text-[#6B7280]" />
                      <span>Message History ({ticketDetail.messages.length})</span>
                    </h4>

                    {ticketDetail.messages.length === 0 ? (
                      <div className="rounded-md border border-dashed border-[#E5E7EB] p-6 text-center text-xs text-[#6B7280]">
                        No messages logged for this thread.
                      </div>
                    ) : (
                      ticketDetail.messages.map((msg) => {
                        const isInbound = msg.direction === "in";
                        return (
                          <div
                            key={msg.id}
                            className={`rounded-lg border p-4 text-xs transition-colors ${
                              isInbound
                                ? "border-[#E5E7EB] bg-white"
                                : "border-[#E5E7EB] bg-[#F5F5F5]/60"
                            }`}
                          >
                            <div className="mb-2 flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <span
                                  className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] ${
                                    isInbound
                                      ? "bg-[#F5F5F5] text-[#111111] border border-[#E5E7EB]"
                                      : "bg-[#111111] text-white"
                                  }`}
                                >
                                  {isInbound ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
                                </span>
                                <span className="font-medium text-[#111111]">
                                  {msg.from_address}
                                </span>
                                <span className="rounded bg-[#F5F5F5] border border-[#E5E7EB] px-1.5 py-0.2 text-[10px] uppercase font-mono text-[#6B7280]">
                                  {msg.direction === "in" ? "Inbound (Customer)" : "Outbound (AI / Agent)"}
                                </span>
                              </div>
                              <span className="font-mono text-[#6B7280] text-[11px]">
                                {formatDate(msg.created_at)}
                              </span>
                            </div>

                            <div className="text-[#333333] whitespace-pre-wrap font-sans text-xs leading-relaxed pl-7">
                              {msg.body}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </>
              )}
            </DialogContent>

            <DialogFooter>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedTicketId(null)}
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
