"use client";

import * as React from "react";
import { ApprovalItem, approvalsApi } from "@/lib/approvals";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ShieldAlert, CheckCircle2, XCircle, Clock, AlertTriangle, RefreshCw } from "lucide-react";

export function ApprovalQueue() {
  const [items, setItems] = React.useState<ApprovalItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [processingId, setProcessingId] = React.useState<string | null>(null);
  const [editedReplies, setEditedReplies] = React.useState<Record<string, string>>({});
  const [reviewNotes, setReviewNotes] = React.useState<Record<string, string>>({});

  const loadApprovals = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await approvalsApi.getPending();
      setItems(data);
      const initialReplies: Record<string, string> = {};
      data.forEach((item) => {
        if (item.proposed_reply) {
          initialReplies[item.id] = item.proposed_reply;
        }
      });
      setEditedReplies(initialReplies);
    } catch (err: any) {
      setError(err.message || "Failed to load pending approvals");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadApprovals();
  }, [loadApprovals]);

  const handleApprove = async (item: ApprovalItem) => {
    try {
      setProcessingId(item.id);
      await approvalsApi.approve(
        item.id,
        "supervisor",
        reviewNotes[item.id] || "Approved via dashboard",
        editedReplies[item.id]
      );
      setItems((prev) => prev.filter((i) => i.id !== item.id));
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (item: ApprovalItem) => {
    const reason = prompt("Enter rejection reason for customer / logs:", "Policy exception denied");
    if (!reason) return;

    try {
      setProcessingId(item.id);
      await approvalsApi.reject(item.id, "supervisor", reason);
      setItems((prev) => prev.filter((i) => i.id !== item.id));
    } catch (err: any) {
      alert(`Rejection error: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const getActionBadge = (actionType: string) => {
    if (actionType.includes("refund")) {
      return <Badge className="bg-amber-500 hover:bg-amber-600 text-white">Financial Refund</Badge>;
    }
    if (actionType.includes("replacement")) {
      return <Badge className="bg-blue-600 hover:bg-blue-700 text-white">Hardware Replacement</Badge>;
    }
    if (actionType.includes("rma")) {
      return <Badge className="bg-purple-600 hover:bg-purple-700 text-white">RMA Exception</Badge>;
    }
    return <Badge className="bg-gray-700 text-white">{actionType}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-[#111111]">
            Supervisor Approval Queue
          </h2>
          <p className="text-sm text-gray-500">
            Review and authorize high-stakes agent actions (refunds, device replacements, policy exceptions).
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadApprovals}
          disabled={loading}
          className="flex items-center gap-1.5"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {loading && items.length === 0 ? (
        <div className="flex h-40 items-center justify-center">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      ) : items.length === 0 ? (
        <Card className="border-dashed border-gray-300 bg-gray-50/50">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <CheckCircle2 className="h-10 w-10 text-emerald-500 mb-2" />
            <h3 className="font-semibold text-gray-800">Queue is Clear</h3>
            <p className="text-sm text-gray-500 max-w-sm mt-1">
              No autonomous agent actions currently require human supervisor review.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {items.map((item) => {
            const isProcessing = processingId === item.id;
            return (
              <Card key={item.id} className="border-l-4 border-l-amber-500 shadow-sm">
                <CardHeader className="pb-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="h-5 w-5 text-amber-500" />
                      <CardTitle className="text-base font-semibold">
                        Action: <span className="font-mono text-sm">{item.action_type}</span>
                      </CardTitle>
                      {getActionBadge(item.action_type)}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Clock className="h-3.5 w-3.5" />
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                  <CardDescription className="text-xs">
                    Thread ID: <span className="font-mono">{item.thread_id}</span>
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4 pt-1">
                  {/* Action Arguments / Payload */}
                  <div className="rounded-md bg-gray-50 p-3 text-xs font-mono border border-gray-200">
                    <span className="font-bold text-gray-700 block mb-1">Tool Arguments:</span>
                    <pre className="overflow-x-auto text-gray-800">
                      {JSON.stringify(item.payload, null, 2)}
                    </pre>
                  </div>

                  {/* Proposed Reply Draft */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-gray-700">
                      Proposed Reply to Customer (Supervisor may edit before approval):
                    </label>
                    <Textarea
                      rows={4}
                      value={editedReplies[item.id] || ""}
                      onChange={(e) =>
                        setEditedReplies({ ...editedReplies, [item.id]: e.target.value })
                      }
                      className="text-xs font-sans bg-white border-gray-300"
                      placeholder="Agent draft reply..."
                    />
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-gray-100">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleReject(item)}
                      disabled={isProcessing}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                    >
                      <XCircle className="h-4 w-4 mr-1.5" />
                      Reject Action
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleApprove(item)}
                      disabled={isProcessing}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white"
                    >
                      <CheckCircle2 className="h-4 w-4 mr-1.5" />
                      Approve & Execute
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

