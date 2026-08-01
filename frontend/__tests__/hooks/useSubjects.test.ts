import { createElement } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  useSubjects,
  useSubject,
  useCreateSubject,
  useUpdateSubject,
  useDeleteSubject,
} from "@/hooks/useSubjects";
import * as subjectService from "@/services/subject.service";

vi.mock("@/services/subject.service");

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

const mockSubjects = [
  { id: 1, teacher_id: 1, name: "English 101", created_at: "2024-01-01T00:00:00Z" },
  { id: 2, teacher_id: 1, name: "History 201", created_at: "2024-01-02T00:00:00Z" },
];

describe("useSubjects", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns the teacher's subjects once the request resolves", async () => {
    vi.mocked(subjectService.getSubjects).mockResolvedValue(mockSubjects);

    const { result } = renderHook(() => useSubjects(), { wrapper: createWrapper() });

    expect(result.current.isPending).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockSubjects);
  });

  it("surfaces an error when the request fails", async () => {
    vi.mocked(subjectService.getSubjects).mockRejectedValue(new Error("boom"));

    const { result } = renderHook(() => useSubjects(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
  });
});

describe("useSubject", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches a single subject by id", async () => {
    vi.mocked(subjectService.getSubject).mockResolvedValue(mockSubjects[0]);

    const { result } = renderHook(() => useSubject(1), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(subjectService.getSubject).toHaveBeenCalledWith(1);
    expect(result.current.data).toEqual(mockSubjects[0]);
  });

  it("does not fire a request for a non-numeric id", () => {
    renderHook(() => useSubject(Number("abc")), { wrapper: createWrapper() });

    expect(subjectService.getSubject).not.toHaveBeenCalled();
  });

  it("does not retry another teacher's subject (plain 404)", async () => {
    vi.mocked(subjectService.getSubject).mockRejectedValue({
      isAxiosError: true,
      response: { status: 404, data: { detail: "Subject 5 not found" } },
    });

    const { result } = renderHook(() => useSubject(5), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(subjectService.getSubject).toHaveBeenCalledTimes(1);
  });
});

describe("subject mutations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("useCreateSubject posts the new name", async () => {
    const created = {
      id: 3,
      teacher_id: 1,
      name: "Science 301",
      created_at: "2024-01-03T00:00:00Z",
    };
    vi.mocked(subjectService.createSubject).mockResolvedValue(created);

    const { result } = renderHook(() => useCreateSubject(), { wrapper: createWrapper() });

    await act(async () => {
      const returned = await result.current.mutateAsync({ name: "Science 301" });
      expect(returned).toEqual(created);
    });

    expect(subjectService.createSubject).toHaveBeenCalledWith({ name: "Science 301" });
  });

  it("useUpdateSubject splits the id out of the payload", async () => {
    vi.mocked(subjectService.updateSubject).mockResolvedValue({
      ...mockSubjects[0],
      name: "English 102",
    });

    const { result } = renderHook(() => useUpdateSubject(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync({ id: 1, name: "English 102" });
    });

    expect(subjectService.updateSubject).toHaveBeenCalledWith(1, { name: "English 102" });
  });

  it("useDeleteSubject deletes by id", async () => {
    vi.mocked(subjectService.deleteSubject).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteSubject(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync(2);
    });

    expect(subjectService.deleteSubject).toHaveBeenCalledWith(2);
  });

  it("surfaces a mutation error instead of throwing unhandled", async () => {
    vi.mocked(subjectService.createSubject).mockRejectedValue(new Error("nope"));

    const { result } = renderHook(() => useCreateSubject(), { wrapper: createWrapper() });

    await act(async () => {
      await expect(result.current.mutateAsync({ name: "x" })).rejects.toThrow("nope");
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
