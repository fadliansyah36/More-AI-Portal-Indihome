import { redirect } from 'next/navigation';

export default function OnboardingRoute() {
  redirect('/?view=onboarding');
}
