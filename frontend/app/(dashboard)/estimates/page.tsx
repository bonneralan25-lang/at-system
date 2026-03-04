"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type Estimate, type EstimateStatus } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const statusVariant: Record<EstimateStatus, "pending" | "success" | "destructive" | "warning"> = {
  pending: "pending",
  approved: "success",
  rejected: "destructive",
  adjusted: "warning",
};

const serviceLabel: Record<string, string> = {
  fence_staining: "Fence Staining",
  pressure_washing: "Pressure Washing",
};

export default function EstimatesPage() {
  const [estimates, setEstimates] = useState<Estimate[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<EstimateStatus | "all">("pending");

  useEffect(() => {
    const params = statusFilter !== "all" ? `status=${statusFilter}` : "";
    api.getEstimates(params)
      .then(setEstimates)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [statusFilter]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Estimates</h1>
        <p className="text-muted-foreground">Review, approve, or reject generated estimates</p>
      </div>

      {/* Status filter */}
      <div className="flex gap-2 flex-wrap">
        {(["pending", "approved", "adjusted", "rejected", "all"] as const).map((s) => (
          <Button
            key={s}
            size="sm"
            variant={statusFilter === s ? "default" : "outline"}
            onClick={() => { setStatusFilter(s); setLoading(true); }}
          >
            {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
          </Button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-lg bg-muted animate-pulse" />
          ))}
        </div>
      ) : estimates.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No {statusFilter !== "all" ? statusFilter : ""} estimates yet.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {estimates.map((est) => (
            <Card key={est.id} className="hover:shadow-md transition-shadow">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{serviceLabel[est.service_type]}</span>
                      <Badge variant={statusVariant[est.status]}>{est.status}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {est.lead?.address ?? "Address pending"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Created {formatDate(est.created_at)}
                      {est.approved_at && ` · Approved ${formatDate(est.approved_at)}`}
                    </p>
                  </div>
                  <div className="text-right space-y-2">
                    <p className="font-bold text-xl">
                      {formatCurrency(est.estimate_low)}–{formatCurrency(est.estimate_high)}
                    </p>
                    <Button size="sm" asChild>
                      <Link href={`/estimates/${est.id}`}>
                        {est.status === "pending" ? "Review" : "View"}
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
