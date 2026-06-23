import { Card, CardBody, CardHeader, Skeleton } from "./ui";

export function ProfileSkeleton() {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <Skeleton className="h-3.5 w-24" />
          <Skeleton className="h-5 w-24" />
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="grid grid-cols-[160px_1fr] gap-4 sm:grid-cols-[200px_1fr]"
              >
                <Skeleton className="h-3.5 w-20" />
                <Skeleton className="h-3.5 w-3/4" />
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
      <Card>
        <CardHeader>
          <Skeleton className="h-3.5 w-24" />
          <Skeleton className="h-3 w-16" />
        </CardHeader>
        <CardBody className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-9 w-full" />
          ))}
        </CardBody>
      </Card>
    </div>
  );
}
