import { redirect } from 'next/navigation';

export default function QueueRedirect() {
  // Redirect /dashboard/queue to /dashboard/cases
  redirect('/dashboard/cases');
}
