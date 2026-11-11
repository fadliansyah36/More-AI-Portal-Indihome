import { redirect } from 'next/navigation';

export default function CustomerRegisterRoute() {
  redirect('/?view=register');
}
