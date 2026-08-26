const fs = require('fs');

let content = fs.readFileSync('src/app/analyze/page.tsx', 'utf8');

const newFetch = `      const body: Record<string, unknown> = {};
      if (demoParam) {
        body.demo = true;
        body.owner = "demo";
        body.name = "demo";
      } else if (parsed) {
        body.owner = parsed.owner;
        body.name = parsed.name;
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
      
      let response;
      try {
        response = await fetch(\`\${apiUrl}/analyze\`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      } catch (err) {
        throw new Error("Python analysis backend is unavailable");
      }

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("repository not found");
        }
        if (response.status === 403) {
          throw new Error("GitHub rate limit exceeded");
        }
        // Show actual backend error message when available
        throw new Error(data.detail || data.error || "Analysis failed");
      }`;

content = content.replace(/const body: Record<string, unknown> = \{\};[\s\S]*?if \(!response\.ok\) \{[\s\S]*?throw new Error\(data\.error \|\| "Analysis failed"\);[\s\S]*?\}/, newFetch);

fs.writeFileSync('src/app/analyze/page.tsx', content);
console.log("Patched page.tsx");
