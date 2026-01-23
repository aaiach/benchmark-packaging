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
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-white/10 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="glass-panel w-full max-w-6xl max-h-[90vh] overflow-hidden shadow-2xl flex flex-col bg-white/80 border-white/60"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100 bg-white/50 backdrop-blur-md">
          <div>
            <Badge className="mb-2 shadow-sm">{product.brand}</Badge>
            <h2 className="text-2xl font-bold text-gray-900">{product.name}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500 hover:text-gray-900"
          >
            <X size={24} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 px-6 pt-4 border-b border-gray-100 bg-white/30">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-5 py-3 text-sm font-semibold rounded-t-xl transition-all',
                activeTab === tab.id
                  ? 'bg-white text-blue-600 shadow-sm border-t border-x border-gray-100 translate-y-[1px]'
                  : 'text-gray-500 hover:text-gray-800 hover:bg-white/40'
              )}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8 bg-white/20">
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
        <div className="relative group aspect-[4/5] rounded-2xl overflow-hidden border border-white/60 bg-white/40 shadow-sm">
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-full object-contain p-8 transition-opacity duration-300 group-hover:opacity-0 mix-blend-multiply"
          />
          <img
            src={product.heatmap}
            alt="Heatmap"
            className="absolute inset-0 w-full h-full object-contain p-8 opacity-0 group-hover:opacity-100 transition-opacity duration-300 mix-blend-multiply"
          />
          <div className="absolute bottom-4 left-4 bg-white/90 px-4 py-2 rounded-full text-xs font-medium text-gray-700 pointer-events-none flex items-center gap-2 shadow-lg backdrop-blur-xl border border-white/50">
            <Eye size={14} className="text-blue-500" />
            Survolez pour la Heatmap d'Attention
          </div>
        </div>

        {/* Key Differentiator */}
        {product.key_differentiator && (
          <div className="bg-gradient-to-r from-blue-50/80 to-purple-50/80 border border-blue-100 rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-2 text-blue-600 text-xs font-bold uppercase tracking-wider mb-2">
              <Sparkles size={14} />
              Différenciateur Clé
            </div>
            <div className="text-gray-800 font-medium leading-relaxed">{product.key_differentiator}</div>
          </div>
        )}
      </div>

      {/* Right Column */}
      <div className="space-y-8">
        {/* Positioning */}
        <div>
          <SectionTitle icon={Target}>Positionnement Stratégique</SectionTitle>
          <p className="text-gray-600 leading-relaxed bg-white/40 p-4 rounded-xl border border-white/50 shadow-sm">{product.positioning}</p>
        </div>

        {/* Radar Chart */}
        <div className="bg-white/40 p-6 rounded-2xl border border-white/50 shadow-sm">
          <SectionTitle>Radar de Personnalité</SectionTitle>
          <RadarChartWrapper data={chartData} name={product.brand} height={300} color="#3b82f6" />
        </div>

        {/* Trust Signals */}
        <div>
          <SectionTitle icon={ShieldCheck}>Signaux de Confiance</SectionTitle>
          <div className="bg-white/40 p-4 rounded-2xl border border-white/50 shadow-sm">
            <TrustMarkMatrix popStatus={product.pop_status} pointsOfParity={pointsOfParity} />
          </div>
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
          <div className="text-lg font-bold text-gray-900 mb-2">{va.visual_anchor}</div>
          <p className="text-sm text-gray-600 leading-relaxed">{va.visual_anchor_description}</p>
        </Card>

        {/* Eye Tracking */}
        <Card>
          <SectionTitle icon={Eye}>Parcours Oculaire</SectionTitle>
          <EyeTrackingFlow eyeTracking={va.eye_tracking} />
        </Card>


        {/* Typography */}
        <Card>
          <SectionTitle icon={Type}>Typographie</SectionTitle>
          <div className="space-y-4">
            <div className="bg-white/40 p-3 rounded-lg border border-white/50">
              <div className="text-xs text-gray-500 font-bold uppercase tracking-wide mb-1">Cohérence</div>
              <div className="text-sm text-gray-800 font-medium">{va.textual_inventory.typography_consistency}</div>
            </div>
            <div className="bg-white/40 p-3 rounded-lg border border-white/50">
              <div className="text-xs text-gray-500 font-bold uppercase tracking-wide mb-1">Lisibilité</div>
              <div className="text-sm text-gray-600">{va.textual_inventory.readability_assessment}</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Right Column */}
      <div className="space-y-6">
        {/* Color Palette */}
        <Card>
          <SectionTitle icon={Palette}>ADN Couleur</SectionTitle>
          <div className="mb-6">
            <ColorPalette palette={product.palette} />
          </div>
          <div className="pt-4 border-t border-gray-100 space-y-3 bg-white/30 p-4 rounded-xl">
            <div className="flex justify-between text-xs">
              <span className="text-gray-500 font-medium">Finition</span>
              <span className="text-gray-800 font-semibold">{va.chromatic_mapping.surface_finish}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500 font-medium">Harmonie</span>
              <span className="text-gray-800 font-semibold">{va.chromatic_mapping.color_harmony}</span>
            </div>
          </div>
          {va.chromatic_mapping.color_psychology_notes && (
            <p className="mt-4 text-xs text-gray-500 leading-relaxed italic bg-blue-50/50 p-3 rounded-lg border border-blue-100">
              "{va.chromatic_mapping.color_psychology_notes}"
            </p>
          )}
        </Card>

        {/* Claims */}
        <Card>
          <SectionTitle icon={ShieldCheck}>Claims Packaging</SectionTitle>
          <div className="flex flex-wrap gap-2 mb-6">
            {va.textual_inventory.emphasized_claims?.map((claim, idx) => (
              <Badge key={idx} variant="success" className="shadow-sm">
                {claim}
              </Badge>
            ))}
          </div>
          <div className="text-xs text-gray-400 font-bold uppercase tracking-wide mb-2">Tous les claims visibles</div>
          <div className="flex flex-wrap gap-1.5">
            {va.textual_inventory.claims_summary?.map((claim, idx) => (
              <span key={idx} className="text-xs bg-gray-50 px-2 py-1 rounded-md text-gray-500 border border-gray-100">
                {claim}
              </span>
            ))}
          </div>
        </Card>

        {/* Trust Signal Effectiveness */}
        {va.asset_symbolism.trust_signal_effectiveness && (
          <Card>
            <SectionTitle>Efficacité Signaux Confiance</SectionTitle>
            <p className="text-sm text-gray-600 leading-relaxed">
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
          <p className="text-gray-600 leading-relaxed">{va.detailed_analysis}</p>
        </Card>
      )}

      {/* POD Breakdown */}
      <Card>
        <SectionTitle icon={TrendingUp}>Points de Différenciation</SectionTitle>
        <div className="space-y-6">
          {product.pod_scores.map((podScore) => {
            const podDef = pointsOfDifference.find((p) => p.axis_id === podScore.axis_id);
            return (
              <div
                key={podScore.axis_id}
                className="border-b border-gray-100 last:border-0 pb-6 last:pb-0"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="font-bold text-gray-800">
                    {podDef?.axis_name || podScore.axis_id}
                  </div>
                  <div className="w-32 h-2.5 bg-gray-100 rounded-full overflow-hidden shadow-inner">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full"
                      style={{ width: `${podScore.score * 10}%` }}
                    />
                  </div>
                </div>
                <p className="text-sm text-gray-600 leading-relaxed bg-white/40 p-3 rounded-lg border border-white/50">{podScore.reasoning}</p>
                {podDef && (
                  <p className="text-xs text-gray-400 mt-2 italic pl-1">{podDef.description}</p>
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
            <SectionTitle>Storytelling Visuel</SectionTitle>
            <ul className="space-y-3">
              {va.asset_symbolism.visual_storytelling_elements.map((elem, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm text-gray-600 bg-white/40 p-3 rounded-lg border border-white/50">
                  <ChevronRight size={16} className="text-blue-500 mt-0.5 flex-shrink-0" />
                  {elem}
                </li>
              ))}
            </ul>
          </Card>
        )}
    </div>
  );
}
