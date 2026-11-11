import { redirect } from 'next/navigation';

export default function CustomerRoute() {
  redirect('/?view=home');
}
