import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Eye,
  Target,
  Palette,
  Type,
  ShieldCheck,
  Lightbulb,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';
import { api, API_URL } from '../api/client';
import { Spinner, Badge, Card, SectionTitle, Footer } from '../components/atoms';
import { ColorPalette, EyeTrackingFlow } from '../components/molecules';
import type { VisualAnalysis } from '../types';

type TabId = 'visual' | 'strategy';

/**
 * Helper to construct full image URL using API base URL
 */
function getImageUrl(path: string | undefined): string | undefined {
  if (!path) return undefined;
  // If path already starts with http, return as-is
  if (path.startsWith('http')) return path;
  // Otherwise prepend API_URL
  return `${API_URL}${path}`;
}

/**
 * Single image analysis result page.
 * Displays full visual analysis for a completed analysis.
 * This page is result-only - for job progress, see SingleImageProgress.
 */
export function SingleImageResult() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('visual');

  // Load result directly
  useEffect(() => {
    if (!analysisId) return;

    let isMounted = true;

    const fetchResult = async () => {
      try {
        const resultResponse = await api.imageAnalysis.getResult(analysisId);
        if (isMounted) {
          setResult(resultResponse);
          setLoading(false);
        }
      } catch (err: any) {
        if (isMounted) {
          if (err.status === 404) {
            setError('Analyse non trouvée');
          } else if (err.status === 202) {
            // Analysis still in progress - redirect to progress page
            window.location.href = `/analyze/${analysisId}`;
            return;
          } else {
            setError(err.message || 'Erreur lors de la récupération des résultats');
          }
          setLoading(false);
        }
      }
    };

    fetchResult();

    return () => {
      isMounted = false;
    };
  }, [analysisId]);

  // No analysis ID
  if (!analysisId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-8 max-w-md bg-white/50 border-white/60">
          <div className="text-red-500 text-xl mb-4 font-bold">Aucun ID d'analyse fourni</div>
          <Link to="/analyze">
            <button className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors">
              Nouvelle analyse
            </button>
          </Link>
        </Card>
      </div>
    );
  }

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Spinner size="lg" />
          <div className="text-gray-600 text-lg font-medium">Chargement des résultats...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !result) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="text-center py-8 max-w-md bg-white/50 border-white/60">
          <div className="text-red-500 text-xl mb-2 font-bold">Erreur</div>
          <div className="text-gray-500 text-sm mb-6">{error || 'Aucun résultat disponible'}</div>
          <div className="flex gap-4 justify-center">
            <button 
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors flex items-center gap-2"
            >
              <RefreshCw size={16} />
              Réessayer
            </button>
            <Link to="/analyze">
              <button className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors">
                Nouvelle analyse
              </button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Analysis complete - show results
  const analysis = result?.analysis as VisualAnalysis | null;

  if (!analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="text-center py-8 max-w-md bg-white/50 border-white/60">
          <div className="text-gray-500 text-xl mb-4">Aucun résultat disponible</div>
          <Link to="/analyze">
            <button className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors">
              Nouvelle analyse
            </button>
          </Link>
        </Card>
      </div>
    );
  }

  const tabs = [
    { id: 'visual' as TabId, label: 'Analyse Visuelle', icon: Eye },
    { id: 'strategy' as TabId, label: 'Détails Avancés', icon: Lightbulb },
  ];

  return (
    <div className="min-h-screen flex flex-col font-sans">
      <div className="flex-1 p-8 md:p-12">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Back link */}
          <Link 
            to="/analyze" 
            className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft size={16} />
            <span className="text-sm font-medium">Nouvelle analyse</span>
          </Link>

          {/* Header */}
          <header className="space-y-4">
            <div className="flex items-center gap-3">
              <Badge className="shadow-sm">{result?.brand || 'Image'}</Badge>
              <div className="text-sm text-gray-400">
                Score de clarté: {analysis.hierarchy_clarity_score}/10
              </div>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              {result?.product_name || 'Analyse Visuelle'}
            </h1>
          </header>

          {/* Tabs */}
          <div className="flex gap-2 border-b border-gray-100">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-5 py-3 text-sm font-semibold rounded-t-xl transition-all
                  ${activeTab === tab.id
                    ? 'bg-white text-purple-600 shadow-sm border-t border-x border-gray-100 translate-y-[1px]'
                    : 'text-gray-500 hover:text-gray-800 hover:bg-white/40'
                  }
                `}
              >
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="bg-white/20 rounded-2xl">
            {activeTab === 'visual' && (
              <VisualTabContent result={result} analysis={analysis} />
            )}
            {activeTab === 'strategy' && (
              <StrategyTabContent analysis={analysis} />
            )}
          </div>
        </div>
      </div>

      <Footer variant="light" />
    </div>
  );
}

// --- Tab Content Components ---

function VisualTabContent({ result, analysis }: { result: any; analysis: VisualAnalysis }) {
  const imageUrl = getImageUrl(result?.image_url);
  const heatmapUrl = getImageUrl(result?.heatmap_url);

  return (
    <div className="grid md:grid-cols-2 gap-8">
      {/* Left Column */}
      <div className="space-y-6">
        {/* Image Preview with Heatmap Hover */}
        {imageUrl && (
          <Card>
            <div className="relative group aspect-[4/5] rounded-xl overflow-hidden bg-white/40">
              <img
                src={imageUrl}
                alt={result.product_name || 'Analyzed image'}
                className="w-full h-full object-contain p-4 transition-opacity duration-300 group-hover:opacity-0 mix-blend-multiply"
              />
              {heatmapUrl ? (
                <img
                  src={heatmapUrl}
                  alt="Heatmap d'attention"
                  className="absolute inset-0 w-full h-full object-contain p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 mix-blend-multiply"
                />
              ) : (
                <div className="absolute inset-0 w-full h-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gray-100/80">
                  <p className="text-gray-500 text-sm">Heatmap non disponible</p>
                </div>
              )}
              <div className="absolute bottom-4 left-4 bg-white/90 px-4 py-2 rounded-full text-xs font-medium text-gray-700 pointer-events-none flex items-center gap-2 shadow-lg backdrop-blur-xl border border-white/50">
                <Eye size={14} className="text-purple-500" />
                {heatmapUrl ? "Survolez pour la Heatmap d'Attention" : "Image originale"}
              </div>
            </div>
          </Card>
        )}

        {/* Visual Anchor */}
        <Card>
          <SectionTitle icon={Target}>Ancre Visuelle</SectionTitle>
          <div className="text-lg font-bold text-gray-900 mb-2">{analysis.visual_anchor}</div>
          <p className="text-sm text-gray-600 leading-relaxed">{analysis.visual_anchor_description}</p>
        </Card>

        {/* Eye Tracking */}
        <Card>
          <SectionTitle icon={Eye}>Parcours Oculaire</SectionTitle>
          <EyeTrackingFlow eyeTracking={analysis.eye_tracking} />
        </Card>
      </div>

      {/* Right Column */}
      <div className="space-y-6">
        {/* Color Palette */}
        <Card>
          <SectionTitle icon={Palette}>ADN Couleur</SectionTitle>
          <div className="mb-6">
            <ColorPalette palette={analysis.chromatic_mapping.color_palette} />
          </div>
          <div className="pt-4 border-t border-gray-100 space-y-3 bg-white/30 p-4 rounded-xl">
            <div className="flex justify-between text-xs">
              <span className="text-gray-500 font-medium">Finition</span>
              <span className="text-gray-800 font-semibold">{analysis.chromatic_mapping.surface_finish}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500 font-medium">Harmonie</span>
              <span className="text-gray-800 font-semibold">{analysis.chromatic_mapping.color_harmony}</span>
            </div>
          </div>
          {analysis.chromatic_mapping.color_psychology_notes && (
            <p className="mt-4 text-xs text-gray-500 leading-relaxed italic bg-purple-50/50 p-3 rounded-lg border border-purple-100">
              "{analysis.chromatic_mapping.color_psychology_notes}"
            </p>
          )}
        </Card>

        {/* Typography */}
        <Card>
          <SectionTitle icon={Type}>Typographie</SectionTitle>
          <div className="space-y-4">
            <div className="bg-white/40 p-3 rounded-lg border border-white/50">
              <div className="text-xs text-gray-500 font-bold uppercase tracking-wide mb-1">Cohérence</div>
              <div className="text-sm text-gray-800 font-medium">{analysis.textual_inventory.typography_consistency}</div>
            </div>
            <div className="bg-white/40 p-3 rounded-lg border border-white/50">
              <div className="text-xs text-gray-500 font-bold uppercase tracking-wide mb-1">Lisibilité</div>
              <div className="text-sm text-gray-600">{analysis.textual_inventory.readability_assessment}</div>
            </div>
          </div>
        </Card>

        {/* Claims */}
        <Card>
          <SectionTitle icon={ShieldCheck}>Claims Packaging</SectionTitle>
          {analysis.textual_inventory.emphasized_claims && analysis.textual_inventory.emphasized_claims.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {analysis.textual_inventory.emphasized_claims.map((claim, idx) => (
                <Badge key={idx} variant="success" className="shadow-sm">
                  {claim}
                </Badge>
              ))}
            </div>
          )}
          {analysis.textual_inventory.claims_summary && analysis.textual_inventory.claims_summary.length > 0 && (
            <>
              <div className="text-xs text-gray-400 font-bold uppercase tracking-wide mb-2">Tous les claims visibles</div>
              <div className="flex flex-wrap gap-1.5">
                {analysis.textual_inventory.claims_summary.map((claim, idx) => (
                  <span key={idx} className="text-xs bg-gray-50 px-2 py-1 rounded-md text-gray-500 border border-gray-100">
                    {claim}
                  </span>
                ))}
              </div>
            </>
          )}
          {(!analysis.textual_inventory.claims_summary || analysis.textual_inventory.claims_summary.length === 0) && (
            <p className="text-sm text-gray-400 italic">Aucun claim marketing détecté sur ce packaging</p>
          )}
        </Card>
      </div>
    </div>
  );
}

function StrategyTabContent({ analysis }: { analysis: VisualAnalysis }) {
  return (
    <div className="space-y-6">
      {/* Detailed Analysis */}
      {analysis.detailed_analysis && (
        <Card>
          <SectionTitle icon={Lightbulb}>Analyse Visuelle Détaillée</SectionTitle>
          <p className="text-gray-600 leading-relaxed whitespace-pre-line">{analysis.detailed_analysis}</p>
        </Card>
      )}

      {/* Visual Elements */}
      {analysis.elements && analysis.elements.length > 0 && (
        <Card>
          <SectionTitle icon={Target}>Éléments Visuels Détectés</SectionTitle>
          <div className="space-y-4">
            {analysis.elements.map((element, idx) => (
              <div
                key={idx}
                className="flex items-start gap-4 p-4 bg-white/40 rounded-xl border border-white/50"
              >
                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center font-bold text-purple-600">
                  {element.visual_weight}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-gray-800 capitalize">{element.element_type}</span>
                    <span className="text-xs px-2 py-0.5 bg-gray-100 rounded text-gray-500">{element.position}</span>
                  </div>
                  <p className="text-sm text-gray-600">{element.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>Couleur: {element.dominant_color}</span>
                    {element.size_percentage && <span>Taille: ~{element.size_percentage}%</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Trust Signal Effectiveness */}
      {analysis.asset_symbolism?.trust_signal_effectiveness && (
        <Card>
          <SectionTitle icon={ShieldCheck}>Efficacité Signaux Confiance</SectionTitle>
          <p className="text-sm text-gray-600 leading-relaxed">
            {analysis.asset_symbolism.trust_signal_effectiveness}
          </p>
        </Card>
      )}

      {/* Visual Storytelling */}
      {analysis.asset_symbolism?.visual_storytelling_elements &&
        analysis.asset_symbolism.visual_storytelling_elements.length > 0 && (
          <Card>
            <SectionTitle>Storytelling Visuel</SectionTitle>
            <ul className="space-y-3">
              {analysis.asset_symbolism.visual_storytelling_elements.map((elem, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm text-gray-600 bg-white/40 p-3 rounded-lg border border-white/50">
                  <ChevronRight size={16} className="text-purple-500 mt-0.5 flex-shrink-0" />
                  {elem}
                </li>
              ))}
            </ul>
          </Card>
        )}

      {/* Trust Marks */}
      {analysis.asset_symbolism?.trust_marks && analysis.asset_symbolism.trust_marks.length > 0 && (
        <Card>
          <SectionTitle icon={ShieldCheck}>Certifications & Symboles de Confiance</SectionTitle>
          <div className="grid gap-4">
            {analysis.asset_symbolism.trust_marks.map((mark: any, idx: number) => (
              <div
                key={idx}
                className="p-4 bg-white/40 rounded-xl border border-white/50"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-semibold text-gray-800">{mark.name}</span>
                  <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">{mark.mark_type}</span>
                </div>
                <p className="text-sm text-gray-600">{mark.visual_description}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  <span>Position: {mark.position}</span>
                  <span>Importance: {mark.prominence}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
