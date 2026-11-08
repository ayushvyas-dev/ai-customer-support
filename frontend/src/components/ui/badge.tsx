import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold uppercase tracking-wider transition-colors focus:outline-none focus:ring-1 focus:ring-[#111111] focus:ring-offset-1",
  {
    variants: {
      variant: {
        default: "border-[#111111] bg-[#111111] text-white",
        secondary: "border-[#E5E7EB] bg-[#F5F5F5] text-[#333333]",
        destructive: "border-[#333333] bg-[#222222] text-white",
        outline: "border-[#E5E7EB] bg-white text-[#333333]",
        subtle: "border-[#E5E7EB] bg-[#F5F5F5] text-[#4B5563]",
        success: "border-[#111111] bg-[#111111] text-white",
        warning: "border-[#D1D5DB] bg-[#F5F5F5] text-[#111111]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
