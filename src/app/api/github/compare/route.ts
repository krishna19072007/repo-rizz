import { NextRequest, NextResponse } from "next/server";
import { parseGitHubUrl } from "@/lib/validators";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { repo1, repo2 } = body;

    if (!repo1 || !repo2) {
      return NextResponse.json(
        { error: "Please provide both repositories for comparison" },
        { status: 400 }
      );
    }

    const parsed1 = parseGitHubUrl(repo1);
    const parsed2 = parseGitHubUrl(repo2);

    if (!parsed1 || !parsed2) {
      return NextResponse.json(
        { error: "One or both repositories are invalid." },
        { status: 400 }
      );
    }

    // Call Python backend for both repos
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
    
    const [res1, res2] = await Promise.all([
      fetch(`${apiUrl}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ owner: parsed1.owner, name: parsed1.name })
      }),
      fetch(`${apiUrl}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ owner: parsed2.owner, name: parsed2.name })
      })
    ]);

    if (!res1.ok || !res2.ok) {
      const failedRes = !res1.ok ? res1 : res2;
      const data = await failedRes.json().catch(() => ({}));
      return NextResponse.json(
        { error: data.detail || data.error || "Analysis failed for one or both repositories." },
        { status: failedRes.status }
      );
    }

    const data1 = await res1.json();
    const data2 = await res2.json();

    return NextResponse.json({
      repo1: data1.result,
      repo2: data2.result
    });

  } catch (error: any) {
    console.error("Comparison error:", error);
    return NextResponse.json(
      { error: error.message || "An unexpected error occurred during comparison." },
      { status: 500 }
    );
  }
}
