import { redirect } from 'next/navigation';

export default function WorkflowRoute() {
  redirect('/?view=workflow_progress');
}
