"use client";

import Link from "next/link";
import { Card } from "@/components";
import { BaselineUploadForm } from "@/features/papers";

export default function BaselineUploadPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text">Upload a baseline paper</h1>
        <p className="mt-1 text-sm text-text-muted">
          Baseline papers teach the system how a student normally writes. Later
          submissions are compared against this profile.{" "}
          <Link
            href="/papers/analyze"
            className="text-primary-700 hover:underline"
          >
            Upload a submission for analysis instead
          </Link>
        </p>
      </div>

      <Card>
        <BaselineUploadForm />
      </Card>
    </div>
  );
}
