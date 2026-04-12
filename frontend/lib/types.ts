export type SearchMode =
  | "standard"
  | "deep"
  | "evidence"
  | "open_web"
  | "compare_narratives"
  | "private";

export type SearchCategory =
  | "general"
  | "images"
  | "videos"
  | "news"
  | "science"
  | "books"
  | "music"
  | "files";

export interface SearchFilters {
  date_from?: string;
  date_to?: string;
  source_types?: string[];
  language?: string;
  min_credibility?: number;
}

export interface SearchRequest {
  query: string;
  mode?: SearchMode;
  filters?: SearchFilters;
  include_summary?: boolean;
  tor_mode?: boolean;
  offset?: number;
  limit?: number;
}

export interface CategorySearchRequest {
  query: string;
  category: SearchCategory;
  offset?: number;
  limit?: number;
}

export interface SourceInfo {
  source_id?: string;
  domain: string;
  name?: string;
  source_type: string;
  credibility_score: number;
  bias_label: string;
}

export interface SearchResult {
  id: string;
  url: string;
  title: string;
  snippet: string;
  score: number;
  source: SourceInfo;
  evidence_count: number;
  published_at?: string;
  explanation?: Record<string, number>;
  // Media fields
  category?: string;
  thumbnail?: string;
  img_src?: string;
  video_url?: string;
  iframe_src?: string;
  author?: string;
  media_metadata?: Record<string, unknown>;
}

export interface Citation {
  doc_id: string;
  title: string;
  url: string;
  relevance: string;
}

export interface Summary {
  text: string;
  citations: Citation[];
  model_used: string;
  confidence: string;
}

export interface QueryMetadata {
  intent: string;
  mode: string;
  entity_count: number;
  expansion_count: number;
  entities: Array<{ text: string; label: string }>;
  expanded_terms: string[];
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  summary?: Summary;
  query_metadata?: QueryMetadata;
  timing_ms: number;
}

export interface CategorySearchResponse {
  results: SearchResult[];
  total: number;
  category: string;
  timing_ms: number;
}

export interface PerspectiveGroup {
  label: string;
  source_bias: string;
  results: SearchResult[];
  key_claims: string[];
}

export interface CompareResponse {
  query: string;
  perspectives: PerspectiveGroup[];
  summary: string;
  timing_ms: number;
}
