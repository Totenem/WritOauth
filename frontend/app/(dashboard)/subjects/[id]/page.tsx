export default function SubjectDetailPage({ params }: { params: { id: string } }) {
  return (
    <main>
      <h1>Subject #{params.id}</h1>
    </main>
  );
}
