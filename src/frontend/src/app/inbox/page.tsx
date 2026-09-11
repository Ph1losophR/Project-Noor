import { Suspense } from "react";
import InboxView from "./inbox-view";

// Server shell: the view reads its state from the URL on the client, so it
// renders behind a Suspense boundary per the Next.js docs.
export default function InboxPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <InboxView />
    </Suspense>
  );
}
