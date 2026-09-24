"use client";

import { useQuery } from "@tanstack/react-query";
import * as dashboardService from "@/services/dashboard.service";

export const DASHBOARD_QUERY_KEY = ["dashboard", "stats"] as const;

/**
 * Everything the dashboard renders, in one request.
 *
 * Kept deliberately short-lived: a teacher who uploads a paper and returns
 * to the dashboard should see the new numbers, not a minute-old cache.
 */
export function useDashboard() {
  return useQuery({
    queryKey: DASHBOARD_QUERY_KEY,
    queryFn: dashboardService.getDashboardStats,
    staleTime: 10 * 1000,
  });
}
