/**
 * Shared TypeScript types for the application.
 */

// --- Color & Visual Types ---

export type ColorEntry = {
  hex_code: string;
  color_name: string;
  coverage_percentage: number;
  usage: string;
  pantone_approximation?: string | null;
};

export type EyeTracking = {
  pattern_type: string;
  entry_point: string;
  exit_point: string;
  fixation_sequence?: string[];
  dwell_zones?: string[];
};

export type ChromaticMapping = {
  color_palette: ColorEntry[];
  surface_finish: string;
  surface_finish_description?: string;
  color_harmony: string;
  color_psychology_notes: string;
  primary_branding_colors?: string[];
  accent_colors?: string[];
  background_colors?: string[];
};

export type TextualInventory = {
  claims_summary: string[];
  emphasized_claims: string[];
  typography_consistency: string;
  readability_assessment: string;
  all_text_blocks?: any[];
  brand_name_typography?: string;
  product_name_typography?: string;
};

export type AssetSymbolism = {
  trust_marks: any[];
  photography_vs_illustration_ratio: string;
  visual_storytelling_elements: string[];
  trust_signal_effectiveness: string;
  graphical_assets?: any[];
};

export type VisualAnalysis = {
  visual_anchor: string;
  visual_anchor_description: string;
  elements: any[];
  eye_tracking: EyeTracking;
  hierarchy_clarity_score: number;
  detailed_analysis: string;
  massing?: any;
  chromatic_mapping: ChromaticMapping;
  textual_inventory: TextualInventory;
  asset_symbolism: AssetSymbolism;
};

// --- Product Types ---

export type PodScore = {
  axis_id: string;
  score: number;
  reasoning: string;
};

export type PopStatus = {
  pop_id: string;
  has_attribute: boolean;
  evidence: string;
};

export type Product = {
  id: string;
  brand: string;
  name: string;
  image: string;
  image_url?: string;
  local_image_path?: string;
  heatmap: string;
  pod_scores: PodScore[];
  pop_status: PopStatus[];
  positioning: string;
  key_differentiator: string;
  palette: ColorEntry[];
  visual_analysis: VisualAnalysis | null;
};

// --- Category Types ---

export type StrategicInsight = {
  insight_type: string;
  title: string;
  description: string;
  affected_brands: string[];
};

export type PointOfDifference = {
  axis_id: string;
  axis_name: string;
  description: string;
  low_label: string;
  high_label: string;
};

export type PointOfParity = {
  pop_id: string;
  pop_name: string;
  description: string;
};

export type CategoryOverview = {
  id: string;
  name: string;
  summary: string;
  product_count: number;
  points_of_difference: PointOfDifference[];
  points_of_parity: PointOfParity[];
  strategic_insights: StrategicInsight[];
};

export type CategoryListItem = {
  id: string;
  name: string;
  run_id: string;
  product_count: number;
  has_visual_analysis: boolean;
  has_competitive_analysis: boolean;
  analysis_date: string;
};

// --- Job Types ---

export type JobState = 'DRAFT' | 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';

export type JobStatus = {
  job_id: string;
  state: JobState;
  status: string;
  progress?: number;
  current_step?: number;
  step_name?: string;
  result?: any;
  error?: string;
};

// --- Category Data (loaded state) ---

export type CategoryData = {
  overview: CategoryOverview;
  products: Product[];
};
