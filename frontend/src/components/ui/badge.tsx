import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium transition-all duration-200 border",
  {
    variants: {
      variant: {
        default:
          "border-border bg-muted text-muted-foreground",
        secondary:
          "border-border bg-secondary text-secondary-foreground",
        destructive:
          "border-destructive/20 bg-destructive/8 text-destructive",
        outline: "text-foreground border-border hover:bg-accent",
        success:
          "border-primary/20 bg-primary/8 text-primary",
        warning:
          "border-border bg-accent text-foreground",
        info:
          "border-border bg-secondary text-secondary-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge }
