import { request } from "./api";

export interface ApprovalItem {
  id: string;
  thread_id: string;
  action_type: string;
  payload: Record<string, any>;
  status: "pending" | "approved" | "rejected";
  proposed_reply?: string;
  created_at: string;
  resolved_at?: string;
  resolved_by?: string;
}

export const approvalsApi = {
  async getPending(): Promise<ApprovalItem[]> {
    return request<ApprovalItem[]>("/api/approvals/pending");
  },

  async approve(
    approvalId: string,
    reviewer: string = "supervisor",
    notes?: string,
    editedReply?: string
  ): Promise<{ status: string; approval_id: string }> {
    return request(`/api/approvals/${approvalId}/approve`, {
      method: "POST",
      body: JSON.stringify({ reviewer, notes, edited_reply: editedReply }),
    });
  },

  async reject(
    approvalId: string,
    reviewer: string = "supervisor",
    notes?: string
  ): Promise<{ status: string; approval_id: string }> {
    return request(`/api/approvals/${approvalId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reviewer, notes }),
    });
  },
};

