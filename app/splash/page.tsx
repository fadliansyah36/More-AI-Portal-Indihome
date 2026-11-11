import { redirect } from 'next/navigation';

export default function SplashRoute() {
  redirect('/?view=splash');
}
