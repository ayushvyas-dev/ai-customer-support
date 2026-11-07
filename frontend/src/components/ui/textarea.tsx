import * as React from "react";
import { cn } from "@/lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-[#E5E7EB] bg-white px-3 py-2 text-sm text-[#111111] shadow-2xs placeholder:text-[#9CA3AF] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#111111] focus-visible:border-[#111111] disabled:cursor-not-allowed disabled:opacity-50 font-mono transition-colors",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";

export { Textarea };
