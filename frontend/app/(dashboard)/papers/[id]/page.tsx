"use client";

import Link from "next/link";
import { PaperDetail } from "@/features/papers";

export default function PaperDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="space-y-6">
      <div>
        <Link href="/papers/analyze" className="text-sm text-primary-700 hover:underline">
          &larr; Back to uploads
        </Link>
        <h1 className="mt-2 text-2xl font-semibold text-text">Paper</h1>
      </div>

      <PaperDetail id={Number(params.id)} />
    </div>
  );
}
