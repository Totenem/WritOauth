import type { DashboardStats } from "@/types";
import api from "./api";

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>("/api/dashboard/stats");
  return data;
}
