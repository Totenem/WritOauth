"use client";

import { PageHeader } from "@/components";
import { DashboardOverview } from "@/features/dashboard";

export default function DashboardPage() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Who's set up, what's been checked, and what needs your attention."
      />
      <DashboardOverview />
    </div>
  );
}
