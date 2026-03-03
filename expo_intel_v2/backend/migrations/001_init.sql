CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS expo_walk_scan (
  scan_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  event_slug text NOT NULL DEFAULT 'natural-products-expo-west-2026',
  company_name text NOT NULL,
  booth_number text,
  hall text,
  category_tags text[] NOT NULL DEFAULT '{}',
  protein_signal_score int NOT NULL CHECK (protein_signal_score BETWEEN 1 AND 5),
  competitive_threat_score int NOT NULL CHECK (competitive_threat_score BETWEEN 1 AND 5),
  follow_up_flag text NOT NULL CHECK (follow_up_flag IN ('revisit','deep_dive','skip')),
  usda_flag boolean NOT NULL DEFAULT false,
  organic_flag boolean NOT NULL DEFAULT false,
  sqf_flag boolean NOT NULL DEFAULT false,
  regenerative_flag boolean NOT NULL DEFAULT false,
  emerging_brand_flag boolean NOT NULL DEFAULT false,
  quick_notes text,
  prs_score int NOT NULL DEFAULT 0 CHECK (prs_score BETWEEN 0 AND 100),
  cti_score int NOT NULL DEFAULT 0 CHECK (cti_score BETWEEN 0 AND 100),
  pos_score int NOT NULL DEFAULT 0 CHECK (pos_score BETWEEN 0 AND 100),
  sps_score int NOT NULL DEFAULT 0 CHECK (sps_score BETWEEN 0 AND 100),
  tier text NOT NULL DEFAULT 'tier3' CHECK (tier IN ('tier1','tier2','tier3')),
  score_confidence text NOT NULL DEFAULT 'medium' CHECK (score_confidence IN ('low','medium','high'))
);

CREATE INDEX IF NOT EXISTS idx_walk_company_booth ON expo_walk_scan(company_name, booth_number);
CREATE INDEX IF NOT EXISTS idx_walk_sps ON expo_walk_scan(sps_score DESC);
CREATE INDEX IF NOT EXISTS idx_walk_category_tags_gin ON expo_walk_scan USING GIN(category_tags);

CREATE TABLE IF NOT EXISTS expo_deep_eval (
  eval_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  event_slug text NOT NULL DEFAULT 'natural-products-expo-west-2026',
  company_name text NOT NULL,
  booth_number text,
  hall text,
  contact_name text,
  contact_email text,
  contact_role text,
  website text,
  core_skus text,
  format_type text,
  pack_size text,
  price_per_unit numeric,
  claims_tags text[] NOT NULL DEFAULT '{}',
  manufacturing_type text NOT NULL CHECK (manufacturing_type IN ('self','co_pack','unknown')),
  certifications text[] NOT NULL DEFAULT '{}',
  estimated_scale text NOT NULL CHECK (estimated_scale IN ('small','mid','national')),
  kill_step_type text,
  channel_presence text[] NOT NULL DEFAULT '{}',
  direct_competitor_flag boolean NOT NULL DEFAULT false,
  closest_charcut_sku text,
  differentiator_notes text,
  weakness_notes text,
  what_they_do_better text,
  what_we_do_better text,
  strategic_fit_score int NOT NULL CHECK (strategic_fit_score BETWEEN 1 AND 5),
  competitive_threat_score int NOT NULL CHECK (competitive_threat_score BETWEEN 1 AND 5),
  partnership_potential_score int NOT NULL CHECK (partnership_potential_score BETWEEN 1 AND 5),
  action_plan text[] NOT NULL DEFAULT '{}',
  post_show_priority text NOT NULL CHECK (post_show_priority IN ('tier1','tier2','tier3')),
  full_notes text,
  prs_score int NOT NULL DEFAULT 0 CHECK (prs_score BETWEEN 0 AND 100),
  cti_score int NOT NULL DEFAULT 0 CHECK (cti_score BETWEEN 0 AND 100),
  pos_score int NOT NULL DEFAULT 0 CHECK (pos_score BETWEEN 0 AND 100),
  sps_score int NOT NULL DEFAULT 0 CHECK (sps_score BETWEEN 0 AND 100),
  tier_suggested text NOT NULL DEFAULT 'tier3' CHECK (tier_suggested IN ('tier1','tier2','tier3')),
  score_confidence text NOT NULL DEFAULT 'high' CHECK (score_confidence IN ('low','medium','high'))
);

CREATE INDEX IF NOT EXISTS idx_eval_company_booth ON expo_deep_eval(company_name, booth_number);
CREATE INDEX IF NOT EXISTS idx_eval_sps ON expo_deep_eval(sps_score DESC);

CREATE TABLE IF NOT EXISTS expo_exhibitors_raw (
  id bigserial PRIMARY KEY,
  created_at timestamptz NOT NULL DEFAULT now(),
  exhibitor_id text,
  name text,
  exhibitor_type text,
  booth text,
  description_html text,
  logo_url text,
  raw_json jsonb NOT NULL DEFAULT '{}'::jsonb
);
