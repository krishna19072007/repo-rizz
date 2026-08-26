import { z } from "zod";

export const githubUrlRegex =
  /^(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9._-]+)\/([a-zA-Z0-9._-]+)(?:\/.*)?$/;
export const shortRepoRegex = /^([a-zA-Z0-9._-]+)\/([a-zA-Z0-9._-]+)$/;

export function parseGitHubUrl(input: string): { owner: string; name: string } | null {
  const trimmed = input.trim();

  // Match full GitHub URL
  const urlMatch = trimmed.match(githubUrlRegex);
  if (urlMatch) {
    return { owner: urlMatch[1], name: urlMatch[2].replace(/\.git$/, "") };
  }

  // Match short form: owner/repo
  const shortMatch = trimmed.match(shortRepoRegex);
  if (shortMatch) {
    return { owner: shortMatch[1], name: shortMatch[2].replace(/\.git$/, "") };
  }

  return null;
}

export const repoInputSchema = z.object({
  input: z.string().min(1, "Please enter a repository URL").refine(
    (val) => parseGitHubUrl(val) !== null,
    "That doesn't look like a valid public GitHub repository."
  ),
});

export type RepoInput = z.infer<typeof repoInputSchema>;
