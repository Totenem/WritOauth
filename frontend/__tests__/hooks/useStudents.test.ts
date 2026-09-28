import { createElement } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  useStudents,
  useStudent,
  useCreateStudent,
  useUpdateStudent,
  useDeleteStudent,
} from "@/hooks/useStudents";
import * as studentService from "@/services/student.service";
import { makeStudent } from "../fixtures/roster";

vi.mock("@/services/student.service");

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

const mockStudents = [
  makeStudent({ id: 1, name: "Ana Cruz" }),
  makeStudent({ id: 2, name: "Ben Reyes" }),
];

describe("useStudents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns the roster once the request resolves", async () => {
    vi.mocked(studentService.getStudents).mockResolvedValue(mockStudents);

    const { result } = renderHook(() => useStudents(), { wrapper: createWrapper() });

    expect(result.current.isPending).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockStudents);
  });

  it("surfaces an error when the request fails", async () => {
    vi.mocked(studentService.getStudents).mockRejectedValue(new Error("boom"));

    const { result } = renderHook(() => useStudents(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
  });
});

describe("useStudent", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches a single student by id", async () => {
    vi.mocked(studentService.getStudent).mockResolvedValue(mockStudents[0]);

    const { result } = renderHook(() => useStudent(1), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(studentService.getStudent).toHaveBeenCalledWith(1);
    expect(result.current.data).toEqual(mockStudents[0]);
  });

  it("does not fire a request for a non-numeric id", () => {
    renderHook(() => useStudent(Number("abc")), { wrapper: createWrapper() });

    expect(studentService.getStudent).not.toHaveBeenCalled();
  });
});

describe("student mutations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("useCreateStudent posts the new student with their courses", async () => {
    const created = makeStudent({ id: 3, name: "Cara Lim" });
    const newStudent = { first_name: "Cara", last_name: "Lim", email: null, subject_ids: [1] };
    vi.mocked(studentService.createStudent).mockResolvedValue(created);

    const { result } = renderHook(() => useCreateStudent(), { wrapper: createWrapper() });

    await act(async () => {
      const returned = await result.current.mutateAsync(newStudent);
      expect(returned).toEqual(created);
    });

    expect(studentService.createStudent).toHaveBeenCalledWith(newStudent);
    await waitFor(() => expect(result.current.data).toEqual(created));
  });

  it("useUpdateStudent splits the id out of the payload", async () => {
    const updated = makeStudent({ id: 1, name: "Ana Cruz-Reyes" });
    vi.mocked(studentService.updateStudent).mockResolvedValue(updated);

    const { result } = renderHook(() => useUpdateStudent(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync({ id: 1, first_name: "Ana", last_name: "Cruz-Reyes", email: null });
    });

    expect(studentService.updateStudent).toHaveBeenCalledWith(1, {
      first_name: "Ana",
      last_name: "Cruz-Reyes",
      email: null,
    });
  });

  it("useDeleteStudent deletes by id", async () => {
    vi.mocked(studentService.deleteStudent).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteStudent(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync(2);
    });

    expect(studentService.deleteStudent).toHaveBeenCalledWith(2);
  });

  it("surfaces a mutation error instead of throwing unhandled", async () => {
    vi.mocked(studentService.createStudent).mockRejectedValue(new Error("nope"));

    const { result } = renderHook(() => useCreateStudent(), { wrapper: createWrapper() });

    await act(async () => {
      await expect(result.current.mutateAsync({ first_name: "x", last_name: "y", email: null, subject_ids: [1] })).rejects.toThrow("nope");
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
