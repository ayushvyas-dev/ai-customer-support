import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#111111] focus-visible:ring-offset-1 disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
  {
    variants: {
      variant: {
        default:
          "bg-[#111111] text-white border border-[#111111] hover:bg-[#222222] hover:border-[#222222] active:bg-[#000000]",
        destructive:
          "bg-[#111111] text-white border border-[#333333] hover:bg-[#222222] active:bg-[#000000]",
        outline:
          "border border-[#E5E7EB] bg-white text-[#111111] hover:bg-[#F5F5F5] hover:border-[#D1D5DB] active:bg-[#E5E7EB]",
        secondary:
          "border border-[#E5E7EB] bg-[#F5F5F5] text-[#111111] hover:bg-[#E5E7EB] hover:border-[#D1D5DB] active:bg-[#D1D5DB]",
        ghost:
          "text-[#6B7280] hover:bg-[#F5F5F5] hover:text-[#111111] border border-transparent",
        link:
          "text-[#111111] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
