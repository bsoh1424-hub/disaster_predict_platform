import { NextResponse } from "next/server";
import { mockPredictions } from "../../../lib/mock/forecast";

export async function GET() {
  return NextResponse.json(mockPredictions);
}
