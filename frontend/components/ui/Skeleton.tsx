import { cn } from "@/lib/utils";
export function Skeleton({
    className,
    ...props
}: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div
            className={cn("animate-pulse rounded-md bg-cyber-slate-800/80", className)}
            {...props}
        />
    );
}
