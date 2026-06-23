import * as React from "react";
import { cn } from "@/lib/cn";

export function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("card", className)} {...props} />;
}

export function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex items-center justify-between border-b border-hairline px-5 py-4",
        className,
      )}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn(
        "text-sm font-semibold uppercase tracking-[0.08em] text-muted",
        className,
      )}
      {...props}
    />
  );
}

export function CardBody({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 py-4", className)} {...props} />;
}

export type BadgeTone =
  | "neutral"
  | "brand"
  | "amber"
  | "red"
  | "green"
  | "restricted";

export function Badge({
  tone = "neutral",
  className,
  children,
  icon,
}: {
  tone?: BadgeTone;
  className?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
}) {
  const toneClass: Record<BadgeTone, string> = {
    neutral: "border-hairline bg-white text-ink/80",
    brand: "border-brand/20 bg-brand-tint text-brand-dark",
    amber: "border-status-amber/30 bg-amber-50 text-status-amber",
    red: "border-status-red/30 bg-red-50 text-status-red",
    green: "border-brand/30 bg-brand-tint text-brand-dark",
    restricted: "border-status-red/30 bg-red-50 text-status-red",
  };
  return (
    <span className={cn("pill", toneClass[tone], className)}>
      {icon}
      {children}
    </span>
  );
}

export function Skeleton({
  className,
}: {
  className?: string;
}) {
  return (
    <div className={cn("skeleton-shimmer rounded-md", className)} />
  );
}

export function KeyValue({
  label,
  altLabel,
  value,
  mono = false,
}: {
  label: string;
  altLabel?: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="grid grid-cols-[160px_1fr] gap-4 py-2.5 sm:grid-cols-[200px_1fr]">
      <dt className="text-sm text-muted">
        {label}
        {altLabel ? (
          <span className="ml-1.5 text-muted/70" lang="bn">
            {altLabel}
          </span>
        ) : null}
      </dt>
      <dd
        className={cn(
          "text-sm text-ink",
          mono && "font-mono tabular text-[0.9rem]",
        )}
      >
        {value}
      </dd>
    </div>
  );
}
