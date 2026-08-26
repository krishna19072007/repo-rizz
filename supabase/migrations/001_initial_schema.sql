-- Repo Rizz Database Schema

-- Profiles table (for Supabase Auth)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT,
  display_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Repositories table
CREATE TABLE IF NOT EXISTS repositories (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  owner TEXT NOT NULL,
  name TEXT NOT NULL,
  full_name TEXT NOT NULL UNIQUE,
  description TEXT,
  url TEXT NOT NULL,
  language TEXT,
  stars INTEGER DEFAULT 0,
  forks INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analyses table
CREATE TABLE IF NOT EXISTS analyses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  repository_id UUID REFERENCES repositories(id),
  user_id UUID REFERENCES profiles(id),
  health_score INTEGER NOT NULL,
  health_status TEXT NOT NULL,
  health_summary TEXT,
  rizz_verdict TEXT,
  resume_score INTEGER,
  ai_summary TEXT,
  ai_rizz_verdict TEXT,
  ai_unavailable BOOLEAN DEFAULT FALSE,
  analysis_time_ms INTEGER,
  is_demo BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analysis Dimensions table
CREATE TABLE IF NOT EXISTS analysis_dimensions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
  dimension_id TEXT NOT NULL,
  dimension_name TEXT NOT NULL,
  score INTEGER NOT NULL,
  weight INTEGER NOT NULL,
  status TEXT NOT NULL,
  summary TEXT,
  recommendation TEXT,
  evidence JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Findings table
CREATE TABLE IF NOT EXISTS findings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
  dimension_id TEXT NOT NULL,
  severity TEXT NOT NULL,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  evidence JSONB DEFAULT '[]',
  file_path TEXT,
  recommendation TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
  priority TEXT NOT NULL,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  impact TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_analyses_repository ON analyses(repository_id);
CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dimensions_analysis ON analysis_dimensions(analysis_id);
CREATE INDEX IF NOT EXISTS idx_findings_analysis ON findings(analysis_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_analysis ON recommendations(analysis_id);
CREATE INDEX IF NOT EXISTS idx_repositories_full_name ON repositories(full_name);

-- Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_dimensions ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Public repos viewable" ON repositories FOR SELECT USING (true);
CREATE POLICY "Analyses viewable by owner or public" ON analyses FOR SELECT USING (user_id IS NULL OR auth.uid() = user_id);
