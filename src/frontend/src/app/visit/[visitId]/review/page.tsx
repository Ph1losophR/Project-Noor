import { Suspense } from "react";
import ReviewView from "./review-view";

// Server shell: the view reads the visit id and day from the URL on the
// client, so it renders behind a Suspense boundary per the Next.js docs.
export default function ReviewPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <ReviewView />
    </Suspense>
  );
}
