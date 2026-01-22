import competitiveData from './lait_davoine_competitive_analysis_20260120_184854.json';
import visualData from './lait_davoine_visual_analysis_20260120_184854.json';

// --- Types derived directly from the JSON structure ---

export type ColorEntry = {
  color_name: string;
  hex_code: string;
  pantone_approximation: string | null;
  usage: string;
  coverage_percentage: number;
}

export type EyeTracking = {
  pattern_type: string;
  entry_point: string;
  fixation_sequence: string[];
  exit_point: string;
  dwell_zones: string[];
}

export type TrustMark = {
  name: string;
  mark_type: string;
  visual_description: string;
  position: string;
  prominence: string;
  colors: string[];
}

export type VisualElement = {
  element_type: string;
  description: string;
  position: string;
  visual_weight: number;
  dominant_color: string;
  size_percentage: number;
}

export type VisualAnalysis = {
  visual_anchor: string;
  visual_anchor_description: string;
  elements: VisualElement[];
  eye_tracking: EyeTracking;
  hierarchy_clarity_score: number;
  detailed_analysis: string;
  chromatic_mapping: {
    color_palette: ColorEntry[];
    surface_finish: string;
    color_harmony: string;
    color_psychology_notes: string;
  };
  textual_inventory: {
    claims_summary: string[];
    emphasized_claims: string[];
    typography_consistency: string;
    readability_assessment: string;
  };
  asset_symbolism: {
    trust_marks: TrustMark[];
    photography_vs_illustration_ratio: string;
    visual_storytelling_elements: string[];
    trust_signal_effectiveness: string;
  };
}

export type PodScore = {
  axis_id: string;
  score: number;
  reasoning: string;
}

export type PopStatus = {
  pop_id: string;
  has_attribute: boolean;
  evidence: string;
}

export type Product = {
  id: string;
  brand: string;
  name: string;
  image: string;
  heatmap: string;
  pod_scores: PodScore[];
  pop_status: PopStatus[];
  positioning: string;
  key_differentiator: string;
  palette: ColorEntry[];
  visual_analysis: VisualAnalysis | null;
}

export type StrategicInsight = {
  insight_type: string;
  title: string;
  description: string;
  affected_brands: string[];
}

export type PointOfDifference = {
  axis_id: string;
  axis_name: string;
  description: string;
  high_score_indicators: string[];
}

export type PointOfParity = {
  pop_id: string;
  pop_name: string;
  pop_type: string;
  description: string;
}

// --- Data Processing (uses ONLY data from the original JSONs) ---

// Create lookup from competitive data by image_path
const competitiveLookup = new Map(
  competitiveData.products.map((item: any) => [item.image_path, item])
);

// Build products array from visual data (which has all 23 products)
export const products: Product[] = visualData.map((visualEntry: any) => {
  const competitiveEntry = competitiveLookup.get(visualEntry.image_path);
  const analysis = visualEntry.analysis;
  
  // Extract palette directly from visual analysis
  const palette: ColorEntry[] = analysis?.chromatic_mapping?.color_palette || [];

  // Transform image paths for frontend
  const filename = visualEntry.image_path.split('/').pop();
  const imagePath = `/images/lait_davoine/${filename}`;
  
  const namePart = filename?.substring(0, filename.lastIndexOf('.'));
  const extPart = filename?.substring(filename.lastIndexOf('.'));
  const heatmapPath = `/images/lait_davoine/heatmaps/${namePart}_heatmap${extPart}`;

  // Build visual analysis object directly from JSON
  const visualAnalysis: VisualAnalysis | null = analysis ? {
    visual_anchor: analysis.visual_anchor,
    visual_anchor_description: analysis.visual_anchor_description,
    elements: analysis.elements,
    eye_tracking: analysis.eye_tracking,
    hierarchy_clarity_score: analysis.hierarchy_clarity_score,
    detailed_analysis: analysis.detailed_analysis,
    chromatic_mapping: {
      color_palette: analysis.chromatic_mapping?.color_palette || [],
      surface_finish: analysis.chromatic_mapping?.surface_finish || "",
      color_harmony: analysis.chromatic_mapping?.color_harmony || "",
      color_psychology_notes: analysis.chromatic_mapping?.color_psychology_notes || "",
    },
    textual_inventory: {
      claims_summary: analysis.textual_inventory?.claims_summary || [],
      emphasized_claims: analysis.textual_inventory?.emphasized_claims || [],
      typography_consistency: analysis.textual_inventory?.typography_consistency || "",
      readability_assessment: analysis.textual_inventory?.readability_assessment || "",
    },
    asset_symbolism: {
      trust_marks: analysis.asset_symbolism?.trust_marks || [],
      photography_vs_illustration_ratio: analysis.asset_symbolism?.photography_vs_illustration_ratio || "",
      visual_storytelling_elements: analysis.asset_symbolism?.visual_storytelling_elements || [],
      trust_signal_effectiveness: analysis.asset_symbolism?.trust_signal_effectiveness || "",
    }
  } : null;

  return {
    id: visualEntry.brand.toLowerCase().replace(/ /g, '_').replace(/-/g, '_'),
    brand: visualEntry.brand,
    name: visualEntry.product_name,
    image: imagePath,
    heatmap: heatmapPath,
    pod_scores: competitiveEntry?.pod_scores || [],
    pop_status: competitiveEntry?.pop_status || [],
    positioning: competitiveEntry?.positioning_summary || "",
    key_differentiator: competitiveEntry?.key_differentiator || "",
    palette: palette,
    visual_analysis: visualAnalysis
  };
});

// --- Category Level Data (directly from competitive JSON) ---

export const categoryName: string = competitiveData.category;
export const categorySummary: string = competitiveData.category_summary;
export const strategicInsights: StrategicInsight[] = competitiveData.strategic_insights;
export const pointsOfDifference: PointOfDifference[] = competitiveData.points_of_difference;
export const pointsOfParity: PointOfParity[] = competitiveData.points_of_parity;

export const axisDescriptions: Record<string, string> = Object.fromEntries(
  pointsOfDifference.map(pod => [pod.axis_id, pod.axis_name])
);
