import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold uppercase tracking-wider transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-black text-white shadow hover:bg-neutral-800",
        secondary: "border-transparent bg-neutral-100 text-neutral-900 hover:bg-neutral-200",
        destructive: "border-neutral-900 bg-neutral-900 text-white shadow hover:bg-black",
        outline: "text-foreground border-neutral-300",
        subtle: "border-neutral-200 bg-neutral-50 text-neutral-700",
        success: "border-black bg-neutral-900 text-white",
        warning: "border-neutral-400 bg-neutral-200 text-neutral-900",
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

