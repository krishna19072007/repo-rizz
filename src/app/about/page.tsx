import { Metadata } from "next";

export const metadata: Metadata = {
  title: "About | Repo Rizz",
  description: "Learn how Repo Rizz evaluates your GitHub repositories.",
};

export default function AboutPage() {
  return (
    <div className="min-h-screen pt-28 pb-32 px-6" style={{ background: "var(--bg)" }}>
      <div className="max-w-3xl mx-auto space-y-16">
        
        {/* Header Section */}
        <section className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight" style={{ color: "var(--text)" }}>
            ABOUT REPO <span style={{ color: "var(--lime)" }}>RIZZ</span>
          </h1>
          <p className="text-lg font-mono" style={{ color: "var(--lime)" }}>
            "Your repo has some rizz? We'll figure it out......"
          </p>
          <p className="text-base leading-relaxed mt-6 text-left md:text-center" style={{ color: "var(--text-secondary)" }}>
            Repo Rizz is an engineering-focused GitHub repository analyzer built to help developers understand how strong their projects actually are before presenting them to recruiters, faculty, or other developers.
          </p>
        </section>

        {/* What It Does Section */}
        <section className="space-y-4 p-8 rounded-2xl border border-border" style={{ background: "var(--surface)" }}>
          <h2 className="text-xl font-semibold tracking-tight" style={{ color: "var(--text)" }}>WHAT IT DOES</h2>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            Repo Rizz analyzes a public GitHub repository using real repository evidence and turns that information into an understandable engineering report.
          </p>
        </section>

        {/* Primary Areas Section */}
        <section className="space-y-8">
          <h2 className="text-2xl font-semibold tracking-tight text-center" style={{ color: "var(--text)" }}>
            PRIMARY AREAS
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <AreaCard 
              title="Documentation" 
              description="How clearly the project explains itself, including README quality, setup instructions, examples, and supporting documentation." 
            />
            <AreaCard 
              title="Code Quality" 
              description="Signals related to code organization, consistency, configuration, and maintainability." 
            />
            <AreaCard 
              title="Architecture" 
              description="How the repository is structured and how clearly its major technical responsibilities are separated, where applicable." 
            />
            <AreaCard 
              title="Security" 
              description="Repository-level security signals such as security documentation, dependency/security configuration, and exposed-risk indicators." 
            />
            <div className="md:col-span-2">
              <AreaCard 
                title="Resume Readiness" 
                description="A practical assessment of how ready the repository is to present as a portfolio or resume project." 
              />
            </div>
          </div>
        </section>

        {/* Differentiator Section */}
        <section className="space-y-4 p-8 rounded-2xl border border-border" style={{ background: "var(--surface)" }}>
          <h2 className="text-xl font-semibold tracking-tight uppercase" style={{ color: "var(--lime)" }}>
            THAT'S WHAT MAKES REPO RIZZ DIFFERENT
          </h2>
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            Repo Rizz does not treat every repository as the same kind of software. A web application, library, documentation project, or curated open-source resource should not be judged by identical criteria. Repository type and applicability are considered when evaluating the project.
          </p>
        </section>

        {/* How It Works Section */}
        <section className="space-y-8">
          <h2 className="text-2xl font-semibold tracking-tight text-center" style={{ color: "var(--text)" }}>
            HOW IT WORKS
          </h2>
          <div className="flex flex-col items-center space-y-3 font-mono text-sm max-w-sm mx-auto p-8 rounded-2xl border border-border" style={{ background: "var(--surface-elevated)", color: "var(--text)" }}>
            <div>GitHub Repository</div>
            <div style={{ color: "var(--lime)" }}>↓</div>
            <div>Real Repository Data</div>
            <div style={{ color: "var(--lime)" }}>↓</div>
            <div>Python/FastAPI Analysis</div>
            <div style={{ color: "var(--lime)" }}>↓</div>
            <div>Evidence Extraction</div>
            <div style={{ color: "var(--lime)" }}>↓</div>
            <div>Scoring Engine</div>
            <div style={{ color: "var(--lime)" }}>↓</div>
            <div>Gemini-Assisted Insights</div>
            <div style={{ color: "var(--lime)" }}>↓</div>
            <div className="font-bold" style={{ color: "var(--lime)" }}>Repo Rizz Report</div>
          </div>
          <p className="text-sm text-center max-w-xl mx-auto" style={{ color: "var(--text-secondary)" }}>
            AI is used to interpret and explain findings, while the underlying repository evidence and scoring logic remain part of the analysis pipeline.
          </p>
        </section>
        
      </div>
    </div>
  );
}

function AreaCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="p-6 rounded-xl border border-border flex flex-col gap-2" style={{ background: "var(--surface)" }}>
      <h3 className="font-semibold" style={{ color: "var(--lime)" }}>{title}</h3>
      <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>{description}</p>
    </div>
  );
}
