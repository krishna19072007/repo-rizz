import { NextRequest, NextResponse } from "next/server";
import { parseGitHubUrl } from "@/lib/validators";
import { demoAnalysisResult } from "@/lib/github/demo";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { input } = body;

    if (!input || typeof input !== "string") {
      return NextResponse.json(
        { error: "Please enter a repository URL or owner/repo" },
        { status: 400 }
      );
    }

    const parsed = parseGitHubUrl(input);
    if (!parsed) {
      return NextResponse.json(
        { error: "That doesn't look like a valid public GitHub repository." },
        { status: 400 }
      );
    }

    // Check for demo request
    if (body.demo) {
      // The result.json has a top-level { result: ... } wrapper
      return NextResponse.json({ result: demoAnalysisResult.result, demo: true });
    }

    const { owner, name } = parsed;

    // Fast proxy to the local Python FastAPI backend
    try {
      const pythonBackendUrl = "http://127.0.0.1:8000/analyze";
      const response = await fetch(pythonBackendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ owner, name })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Python backend error:", errorText);
        return NextResponse.json(
          { error: "The Python analysis engine encountered an error." },
          { status: response.status }
        );
      }

      const data = await response.json();
      return NextResponse.json(data);

    } catch (error) {
      console.error("Failed to connect to Python backend:", error);
      return NextResponse.json(
        { error: "Could not reach the Python backend. Is it running on port 8000?" },
        { status: 503 }
      );
    }
  } catch (error) {
    console.error("Analysis error:", error);
    return NextResponse.json(
      { error: "An unexpected error occurred during analysis." },
      { status: 500 }
    );
  }
}
