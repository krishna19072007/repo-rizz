import { redirect } from "next/navigation";

export default async function RepoPage({
  params,
}: {
  params: Promise<{ owner: string; name: string }>;
}) {
  const { owner, name } = await params;
  redirect(`/analyze?repo=${owner}/${name}`);
}
