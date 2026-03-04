"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, type LeadDetail } from "@/lib/api";
import { formatDate, formatCurrency } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, MapPin, ExternalLink } from "lucide-react";

const GOOGLE_MAPS_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY || "";

const fieldLabels: Record<string, string> = {
  fence_height: "Fence Height",
  fence_age: "Fence Age",
  previously_stained: "Previously Stained",
  timeframe: "Timeframe / Urgency",
  additional_services: "Additional Services",
  additional_notes: "Additional Notes",
  linear_feet: "Linear Feet (VA Estimate)",
  surface_type: "Surface Type",
  square_footage: "Square Footage",
  condition: "Condition",
};

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLead(id).then(setLead).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded-lg" />
      </div>
    );
  }

  if (!lead) {
    return <p className="text-muted-foreground">Lead not found.</p>;
  }

  const mapsEmbedUrl = GOOGLE_MAPS_KEY
    ? `https://www.google.com/maps/embed/v1/place?key=${GOOGLE_MAPS_KEY}&q=${encodeURIComponent(lead.address)}&zoom=19&maptype=satellite`
    : null;

  const mapsLink = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(lead.address)}`;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/leads">
            <ArrowLeft className="h-4 w-4 mr-1" /> Leads
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{lead.address}</h1>
          <p className="text-muted-foreground text-sm">Lead #{lead.id.slice(0, 8)} · {formatDate(lead.created_at)}</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Lead Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Lead Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Service</span>
              <span className="font-medium capitalize">{lead.service_type.replace("_", " ")}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Status</span>
              <Badge>{lead.status}</Badge>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">GHL Contact</span>
              <span className="font-mono text-xs">{lead.ghl_contact_id}</span>
            </div>
            <hr />
            {Object.entries(lead.form_data).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-muted-foreground">{fieldLabels[key] ?? key}</span>
                <span className="font-medium text-right max-w-[200px]">{String(value)}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Google Maps */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <MapPin className="h-4 w-4" /> Property View
              </CardTitle>
              <Button size="sm" variant="outline" asChild>
                <a href={mapsLink} target="_blank" rel="noopener noreferrer">
                  Open Maps <ExternalLink className="ml-1 h-3 w-3" />
                </a>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {mapsEmbedUrl ? (
              <iframe
                src={mapsEmbedUrl}
                className="w-full h-64 rounded-b-lg"
                allowFullScreen
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            ) : (
              <div className="h-64 flex flex-col items-center justify-center gap-3 bg-muted/30 rounded-b-lg">
                <MapPin className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground text-center px-4">
                  Add a Google Maps API key in settings to see satellite view
                </p>
                <Button size="sm" asChild>
                  <a href={mapsLink} target="_blank" rel="noopener noreferrer">
                    Open in Google Maps <ExternalLink className="ml-1 h-3 w-3" />
                  </a>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Estimate Summary */}
      {lead.estimate && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Generated Estimate</CardTitle>
              <Badge variant={
                lead.estimate.status === "approved" ? "success" :
                lead.estimate.status === "rejected" ? "destructive" : "pending"
              }>
                {lead.estimate.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <p className="text-3xl font-bold">
                {formatCurrency(lead.estimate.estimate_low)}–{formatCurrency(lead.estimate.estimate_high)}
              </p>
              <Button asChild>
                <Link href={`/estimates/${lead.estimate.id}`}>
                  {lead.estimate.status === "pending" ? "Review & Approve" : "View Estimate"}
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
