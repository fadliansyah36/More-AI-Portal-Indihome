import { redirect } from 'next/navigation';

export default function CustomerLoginRoute() {
  redirect('/?view=login');
}
