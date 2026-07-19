import { Card, CardContent } from "@/components/ui/card";

export function ListingCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <div className="aspect-[4/3] w-full animate-pulse bg-secondary" />
      <CardContent className="space-y-3 p-4">
        <div className="h-4 w-3/4 animate-pulse rounded bg-secondary" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-secondary" />
        <div className="flex items-center justify-between border-t border-border pt-3">
          <div className="h-3 w-24 animate-pulse rounded bg-secondary" />
          <div className="h-3 w-12 animate-pulse rounded bg-secondary" />
        </div>
      </CardContent>
    </Card>
  );
}
