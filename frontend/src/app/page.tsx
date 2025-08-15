import { redirect } from 'next/navigation';

export default function HomePage() {
  // Redirect to calendar page - this will be the main landing page for logged-in users
  redirect('/calendar');
}