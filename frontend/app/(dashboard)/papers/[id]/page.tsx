export default function PaperDetailPage({ params }: { params: { id: string } }) {
  return (
    <main>
      <h1>Paper #{params.id}</h1>
    </main>
  );
}
