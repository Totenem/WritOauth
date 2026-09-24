"use client";

import { Card, PageHeader } from "@/components";
import { BaselineUploadForm } from "@/features/papers";

export default function BaselineUploadPage() {
  return (
    <div>
      <PageHeader
        title="Add a baseline"
        description="Baselines teach the system how a student normally writes. Give it writing you're confident is theirs — three samples on different topics is the point where comparisons become reliable."
        alternate={{ href: "/papers/analyze", label: "Check a submission instead" }}
      />
      <Card>
        <BaselineUploadForm />
      </Card>
    </div>
  );
}
