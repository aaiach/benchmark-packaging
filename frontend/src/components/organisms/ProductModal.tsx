import React, { useState } from 'react';
import {
  X,
  Eye,
  Target,
  TrendingUp,
  Lightbulb,
  Palette,
  Type,
  ShieldCheck,
  Sparkles,
  ChevronRight,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { Badge, Card, SectionTitle } from '../atoms';
import { ColorPalette, EyeTrackingFlow, RadarChartWrapper, TrustMarkMatrix } from '../molecules';
import type { Product, PointOfDifference, PointOfParity } from '../../types';

type ProductModalProps = {
  product: Product;
  onClose: () => void;
  pointsOfDifference: PointOfDifference[];
  pointsOfParity: PointOfParity[];
  axisDescriptions: Record<string, string>;
};

type TabId = 'overview' | 'visual' | 'strategy';

/**
 * Full-screen product detail modal with tabs.
 */
export function ProductModal({
  product,
  onClose,
  pointsOfDifference,
  pointsOfParity,
  axisDescriptions,
}: ProductModalProps) {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  const chartData = product.pod_scores.map((score) => ({
    subject: axisDescriptions[score.axis_id] || score.axis_id,
    A: score.score,
    fullMark: 10,
  }));

  const va = product.visual_analysis;

  const tabs = [
    { id: 'overview' as TabId, label: 'Vue d\'ensemble', icon: Target },
    { id: 'visual' as TabId, label: 'Analyse Visuelle', icon: Eye },
    { id: 'strategy' as TabId, label: 'Stratégie de Marque', icon: TrendingUp },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-[#0f1729] border border-white/10 w-full max-w-6xl max-h-[90vh] overflow-hidden rounded-2xl shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div>
            <Badge className="mb-2">{product.brand}</Badge>
            <h2 className="text-2xl font-bold text-white">{product.name}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-full transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 pt-4 border-b border-white/10">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-3 text-sm font-medium rounded-t-lg transition-colors',
                activeTab === tab.id
                  ? 'bg-white/10 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              )}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <OverviewTab
              product={product}
              chartData={chartData}
              pointsOfParity={pointsOfParity}
            />
          )}

          {activeTab === 'visual' && va && (
            <VisualTab product={product} va={va} />
          )}

          {activeTab === 'strategy' && (
            <StrategyTab
              product={product}
              va={va}
              pointsOfDifference={pointsOfDifference}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// --- Tab Content Components ---

function OverviewTab({
  product,
  chartData,
  pointsOfParity,
}: {
  product: Product;
  chartData: { subject: string; A: number; fullMark: number }[];
  pointsOfParity: PointOfParity[];
}) {
  return (
    <div className="grid md:grid-cols-2 gap-8">
      {/* Left Column */}
      <div className="space-y-6">
        {/* Product Image with Heatmap */}
        <div className="relative group aspect-[4/5] rounded-xl overflow-hidden border border-white/10 bg-white/5">
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-contain p-4 transition-opacity duration-300 group-hover:opacity-0"
          />
          <img
            src={product.heatmap}
            alt="Heatmap"
            className="absolute inset-0 w-full h-full object-contain p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          />
          <div className="absolute bottom-4 left-4 bg-black/70 px-3 py-1.5 rounded-full text-xs text-white/80 pointer-events-none flex items-center gap-2">
            <Eye size={14} />
            Survolez pour la Heatmap d'Attention
          </div>
        </div>

        {/* Key Differentiator */}
        {product.key_differentiator && (
          <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-lg p-4">
            <div className="flex items-center gap-2 text-blue-300 text-xs uppercase tracking-wider mb-2">
              <Sparkles size={14} />
              Différenciateur Clé
            </div>
            <div className="text-white font-medium">{product.key_differentiator}</div>
          </div>
        )}
      </div>

      {/* Right Column */}
      <div className="space-y-6">
        {/* Positioning */}
        <div>
          <SectionTitle icon={Target}>Positionnement Stratégique</SectionTitle>
          <p className="text-gray-300 leading-relaxed">{product.positioning}</p>
        </div>

        {/* Radar Chart */}
        <div>
          <SectionTitle>Radar de Personnalité de Marque</SectionTitle>
          <RadarChartWrapper data={chartData} name={product.brand} />
        </div>

        {/* Trust Signals */}
        <div>
          <SectionTitle icon={ShieldCheck}>Signaux de Confiance (Points de Parité)</SectionTitle>
          <TrustMarkMatrix popStatus={product.pop_status} pointsOfParity={pointsOfParity} />
        </div>
      </div>
    </div>
  );
}

function VisualTab({ product, va }: { product: Product; va: NonNullable<Product['visual_analysis']> }) {
  return (
    <div className="grid md:grid-cols-2 gap-8">
      {/* Left Column */}
      <div className="space-y-6">
        {/* Visual Anchor */}
        <Card>
          <SectionTitle icon={Target}>Ancre Visuelle</SectionTitle>
          <div className="text-lg font-semibold text-white mb-2">{va.visual_anchor}</div>
          <p className="text-sm text-gray-400 leading-relaxed">{va.visual_anchor_description}</p>
        </Card>

        {/* Eye Tracking */}
        <Card>
          <SectionTitle icon={Eye}>Parcours Oculaire</SectionTitle>
          <EyeTrackingFlow eyeTracking={va.eye_tracking} />
        </Card>


        {/* Typography */}
        <Card>
          <SectionTitle icon={Type}>Évaluation Typographique</SectionTitle>
          <div className="space-y-3">
            <div>
              <div className="text-xs text-gray-500 mb-1">Cohérence</div>
              <div className="text-sm text-white">{va.textual_inventory.typography_consistency}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Lisibilité</div>
              <div className="text-sm text-gray-300">{va.textual_inventory.readability_assessment}</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Right Column */}
      <div className="space-y-6">
        {/* Color Palette */}
        <Card>
          <SectionTitle icon={Palette}>ADN Couleur</SectionTitle>
          <ColorPalette palette={product.palette} />
          <div className="mt-4 pt-4 border-t border-white/10 space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Finition de Surface</span>
              <span className="text-gray-300">{va.chromatic_mapping.surface_finish}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Harmonie Couleurs</span>
              <span className="text-gray-300">{va.chromatic_mapping.color_harmony}</span>
            </div>
          </div>
          {va.chromatic_mapping.color_psychology_notes && (
            <p className="mt-4 text-xs text-gray-400 leading-relaxed italic">
              "{va.chromatic_mapping.color_psychology_notes}"
            </p>
          )}
        </Card>

        {/* Claims */}
        <Card>
          <SectionTitle icon={ShieldCheck}>Claims Packaging</SectionTitle>
          <div className="flex flex-wrap gap-2 mb-4">
            {va.textual_inventory.emphasized_claims?.map((claim, idx) => (
              <Badge key={idx} variant="success">
                {claim}
              </Badge>
            ))}
          </div>
          <div className="text-xs text-gray-500 mb-2">Tous les claims visibles :</div>
          <div className="flex flex-wrap gap-1">
            {va.textual_inventory.claims_summary?.map((claim, idx) => (
              <span key={idx} className="text-xs bg-white/5 px-2 py-1 rounded text-gray-400">
                {claim}
              </span>
            ))}
          </div>
        </Card>

        {/* Trust Signal Effectiveness */}
        {va.asset_symbolism.trust_signal_effectiveness && (
          <Card>
            <SectionTitle>Efficacité des Signaux de Confiance</SectionTitle>
            <p className="text-sm text-gray-300 leading-relaxed">
              {va.asset_symbolism.trust_signal_effectiveness}
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}

function StrategyTab({
  product,
  va,
  pointsOfDifference,
}: {
  product: Product;
  va: Product['visual_analysis'];
  pointsOfDifference: PointOfDifference[];
}) {
  return (
    <div className="space-y-6">
      {/* Detailed Analysis */}
      {va?.detailed_analysis && (
        <Card>
          <SectionTitle icon={Lightbulb}>Analyse Visuelle Détaillée</SectionTitle>
          <p className="text-gray-300 leading-relaxed">{va.detailed_analysis}</p>
        </Card>
      )}

      {/* POD Breakdown */}
      <Card>
        <SectionTitle icon={TrendingUp}>Points de Différenciation</SectionTitle>
        <div className="space-y-4">
          {product.pod_scores.map((podScore) => {
            const podDef = pointsOfDifference.find((p) => p.axis_id === podScore.axis_id);
            return (
              <div
                key={podScore.axis_id}
                className="border-b border-white/5 pb-4 last:border-0 last:pb-0"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium text-white">
                    {podDef?.axis_name || podScore.axis_id}
                  </div>
                  <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${podScore.score * 10}%` }}
                    />
                  </div>
                </div>
                <p className="text-sm text-gray-400">{podScore.reasoning}</p>
                {podDef && (
                  <p className="text-xs text-gray-500 mt-2 italic">{podDef.description}</p>
                )}
              </div>
            );
          })}
        </div>
      </Card>

      {/* Visual Storytelling */}
      {va?.asset_symbolism.visual_storytelling_elements &&
        va.asset_symbolism.visual_storytelling_elements.length > 0 && (
          <Card>
            <SectionTitle>Éléments de Storytelling Visuel</SectionTitle>
            <ul className="space-y-2">
              {va.asset_symbolism.visual_storytelling_elements.map((elem, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                  <ChevronRight size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
                  {elem}
                </li>
              ))}
            </ul>
          </Card>
        )}
    </div>
  );
}
