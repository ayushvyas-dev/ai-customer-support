"use client";

import * as React from "react";
import { ApprovalQueue } from "@/components/ApprovalQueue";

export default function ApprovalsPage() {
  return (
    <div className="container mx-auto max-w-5xl py-8 px-4 sm:px-6">
      <ApprovalQueue />
    </div>
  );
}

