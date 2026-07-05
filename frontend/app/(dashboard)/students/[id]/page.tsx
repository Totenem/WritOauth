export default function StudentDetailPage({ params }: { params: { id: string } }) {
  return (
    <main>
      <h1>Student #{params.id}</h1>
    </main>
  );
}
