import { NextRequest, NextResponse } from 'next/server';

// Legacy provider endpoint intentionally disabled.
// All chat and agent execution must use the authenticated FastAPI boundary.
export async function POST(_request: NextRequest) {
  return NextResponse.json(
    { error: 'This legacy endpoint is disabled. Use the authenticated MoreAI API.' },
    { status: 410 },
  );
}
