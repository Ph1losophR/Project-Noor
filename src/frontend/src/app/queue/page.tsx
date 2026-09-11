import { Suspense } from "react";
import QueueView from "./queue-view";

// Server shell: the view reads the queue on the client, so it renders behind
// a Suspense boundary per the Next.js docs.
export default function QueuePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <QueueView />
    </Suspense>
  );
}
