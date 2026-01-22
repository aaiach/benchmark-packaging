import React, { useState } from 'react';
import { 
  products, 
  axisDescriptions, 
  categoryName, 
  categorySummary, 
  strategicInsights,
  pointsOfDifference,
  pointsOfParity,
} from './data';
import type { Product, ColorEntry } from './data';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { ShieldCheck, Leaf, Globe, Heart, Award, X, Eye, Lightbulb, Palette, Type, Target, TrendingUp, ChevronRight, Sparkles } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- Atomic Components ---

const Card = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn("bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-6 shadow-xl", className)}>
    {children}
  </div>
);

const Badge = ({ children, className, variant = 'default' }: { children: React.ReactNode; className?: string; variant?: 'default' | 'success' | 'outline' | 'info' }) => {
  const variants = {
    default: "bg-white/10 text-white border-white/20",
    success: "bg-green-500/20 text-green-300 border-green-500/30",
    outline: "border-white/30 text-white/70",
    info: "bg-blue-500/20 text-blue-300 border-blue-500/30"
  };
  return (
    <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-medium border inline-flex items-center gap-1", variants[variant], className)}>
      {children}
    </span>
  );
};

const SectionTitle = ({ children, icon: Icon }: { children: React.ReactNode; icon?: any }) => (
  <h3 className="flex items-center gap-2 text-sm uppercase tracking-wider text-gray-400 mb-4 font-medium">
    {Icon && <Icon size={16} className="text-blue-400" />}
    {children}
  </h3>
);

// --- Trust Mark Matrix ---
const TrustMarkMatrix = ({ popStatus }: { popStatus: any[] }) => {
  const icons: Record<string, any> = {
    organic_cert: Leaf,
    no_added_sugar: Heart,
    vegan_claim: Leaf,
    origin_claim: Globe,
    nutri_score: Award,
  };

  const popNames: Record<string, string> = Object.fromEntries(
    pointsOfParity.map(p => [p.pop_id, p.pop_name])
  );

  return (
    <div className="grid grid-cols-1 gap-2">
      {popStatus.map((pop) => {
        const Icon = icons[pop.pop_id] || ShieldCheck;
        return (
          <div key={pop.pop_id} className={cn(
            "flex items-start gap-3 p-3 rounded-lg border transition-all",
            pop.has_attribute 
              ? "bg-green-500/10 border-green-500/20" 
              : "bg-white/5 border-white/10 opacity-50"
          )}>
            <Icon size={16} className={pop.has_attribute ? "text-green-400 mt-0.5" : "text-gray-500 mt-0.5"} />
            <div className="flex-1 min-w-0">
              <div className={cn("text-sm font-medium", pop.has_attribute ? "text-green-100" : "text-gray-400")}>
                {popNames[pop.pop_id] || pop.pop_id.replace(/_/g, ' ')}
              </div>
              {pop.has_attribute && pop.evidence && (
                <div className="text-xs text-gray-400 mt-0.5 truncate">{pop.evidence}</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// --- Enhanced Color Palette ---
const ColorPaletteDetailed = ({ palette }: { palette: ColorEntry[] }) => (
  <div className="space-y-2">
    {palette.slice(0, 5).map((color, idx) => (
      <div key={idx} className="flex items-center gap-3 group">
        <div 
          className="w-8 h-8 rounded-lg border border-white/20 shadow-sm flex-shrink-0" 
          style={{ backgroundColor: color.hex_code }} 
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-white font-medium">{color.color_name}</span>
            <span className="text-xs text-gray-500">{color.hex_code}</span>
          </div>
          <div className="text-xs text-gray-400 truncate">{color.usage}</div>
        </div>
        <div className="text-xs text-gray-500 tabular-nums">{color.coverage_percentage}%</div>
      </div>
    ))}
  </div>
);

// --- Eye Tracking Visualization ---
const EyeTrackingFlow = ({ eyeTracking }: { eyeTracking: any }) => (
  <div className="space-y-3">
    <div className="flex items-center gap-2 text-sm">
      <Badge variant="info">{eyeTracking.pattern_type}-Pattern</Badge>
    </div>
    <div className="text-xs text-gray-400 space-y-1">
      <div><span className="text-gray-300">Entry:</span> {eyeTracking.entry_point}</div>
      <div><span className="text-gray-300">Exit:</span> {eyeTracking.exit_point}</div>
    </div>
    <div className="flex flex-wrap gap-1 mt-2">
      {eyeTracking.fixation_sequence?.map((step: string, idx: number) => (
        <React.Fragment key={idx}>
          <span className="text-xs bg-white/10 px-2 py-1 rounded text-gray-300">{step}</span>
          {idx < eyeTracking.fixation_sequence.length - 1 && (
            <ChevronRight size={12} className="text-gray-600 self-center" />
          )}
        </React.Fragment>
      ))}
    </div>
  </div>
);

// --- Product Modal ---
const ProductModal = ({ product, onClose }: { product: Product; onClose: () => void }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'visual' | 'strategy'>('overview');

  const chartData = product.pod_scores.map((score) => ({
    subject: axisDescriptions[score.axis_id] || score.axis_id,
    A: score.score,
    fullMark: 10,
  }));

  const va = product.visual_analysis;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div 
        className="bg-[#0f1729] border border-white/10 w-full max-w-6xl max-h-[90vh] overflow-hidden rounded-2xl shadow-2xl flex flex-col" 
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div>
            <Badge className="mb-2">{product.brand}</Badge>
            <h2 className="text-2xl font-bold text-white">{product.name}</h2>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 pt-4 border-b border-white/10">
          {[
            { id: 'overview', label: 'Overview', icon: Target },
            { id: 'visual', label: 'Visual Analysis', icon: Eye },
            { id: 'strategy', label: 'Brand Strategy', icon: TrendingUp },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm font-medium rounded-t-lg transition-colors",
                activeTab === tab.id 
                  ? "bg-white/10 text-white border-b-2 border-blue-500" 
                  : "text-gray-400 hover:text-white hover:bg-white/5"
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
            <div className="grid md:grid-cols-2 gap-8">
              {/* Left Column */}
              <div className="space-y-6">
                {/* Product Image with Heatmap */}
                <div className="relative group aspect-[4/5] rounded-xl overflow-hidden border border-white/10 bg-white/5">
                  <img src={product.image} alt={product.name} className="w-full h-full object-contain p-4 transition-opacity duration-300 group-hover:opacity-0" />
                  <img src={product.heatmap} alt="Heatmap" className="absolute inset-0 w-full h-full object-contain p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  <div className="absolute bottom-4 left-4 bg-black/70 px-3 py-1.5 rounded-full text-xs text-white/80 pointer-events-none flex items-center gap-2">
                    <Eye size={14} />
                    Hover for Attention Heatmap
                  </div>
                </div>

                {/* Key Differentiator */}
                {product.key_differentiator && (
                  <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-blue-300 text-xs uppercase tracking-wider mb-2">
                      <Sparkles size={14} />
                      Key Differentiator
                    </div>
                    <div className="text-white font-medium">{product.key_differentiator}</div>
                  </div>
                )}
              </div>

              {/* Right Column */}
              <div className="space-y-6">
                {/* Positioning */}
                <div>
                  <SectionTitle icon={Target}>Strategic Positioning</SectionTitle>
                  <p className="text-gray-300 leading-relaxed">{product.positioning}</p>
                </div>

                {/* Radar Chart */}
                <div>
                  <SectionTitle>Brand Personality Radar</SectionTitle>
                  <div className="h-[280px] -ml-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
                        <PolarGrid stroke="rgba(255,255,255,0.1)" />
                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
                        <Radar name={product.brand} dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.4} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Trust Signals */}
                <div>
                  <SectionTitle icon={ShieldCheck}>Trust Signals (Points of Parity)</SectionTitle>
                  <TrustMarkMatrix popStatus={product.pop_status} />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'visual' && va && (
            <div className="grid md:grid-cols-2 gap-8">
              {/* Left Column */}
              <div className="space-y-6">
                {/* Visual Anchor */}
                <Card>
                  <SectionTitle icon={Target}>Visual Anchor</SectionTitle>
                  <div className="text-lg font-semibold text-white mb-2">{va.visual_anchor}</div>
                  <p className="text-sm text-gray-400 leading-relaxed">{va.visual_anchor_description}</p>
                </Card>

                {/* Eye Tracking */}
                <Card>
                  <SectionTitle icon={Eye}>Eye Tracking Flow</SectionTitle>
                  <EyeTrackingFlow eyeTracking={va.eye_tracking} />
                </Card>

                {/* Hierarchy Score */}
                <Card>
                  <SectionTitle>Visual Hierarchy Clarity</SectionTitle>
                  <div className="flex items-center gap-4">
                    <div className="text-5xl font-bold text-white">{va.hierarchy_clarity_score}</div>
                    <div className="text-gray-400 text-sm">/10</div>
                    <div className="flex-1 h-3 bg-white/10 rounded-full overflow-hidden ml-4">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full transition-all" 
                        style={{ width: `${va.hierarchy_clarity_score * 10}%` }}
                      />
                    </div>
                  </div>
                </Card>

                {/* Typography */}
                <Card>
                  <SectionTitle icon={Type}>Typography Assessment</SectionTitle>
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Consistency</div>
                      <div className="text-sm text-white">{va.textual_inventory.typography_consistency}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Readability</div>
                      <div className="text-sm text-gray-300">{va.textual_inventory.readability_assessment}</div>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Right Column */}
              <div className="space-y-6">
                {/* Color Palette */}
                <Card>
                  <SectionTitle icon={Palette}>Color DNA</SectionTitle>
                  <ColorPaletteDetailed palette={product.palette} />
                  <div className="mt-4 pt-4 border-t border-white/10 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Surface Finish</span>
                      <span className="text-gray-300">{va.chromatic_mapping.surface_finish}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-500">Color Harmony</span>
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
                  <SectionTitle icon={ShieldCheck}>On-Pack Claims</SectionTitle>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {va.textual_inventory.emphasized_claims?.map((claim, idx) => (
                      <Badge key={idx} variant="success">{claim}</Badge>
                    ))}
                  </div>
                  <div className="text-xs text-gray-500 mb-2">All visible claims:</div>
                  <div className="flex flex-wrap gap-1">
                    {va.textual_inventory.claims_summary?.map((claim, idx) => (
                      <span key={idx} className="text-xs bg-white/5 px-2 py-1 rounded text-gray-400">{claim}</span>
                    ))}
                  </div>
                </Card>

                {/* Trust Signal Effectiveness */}
                {va.asset_symbolism.trust_signal_effectiveness && (
                  <Card>
                    <SectionTitle>Trust Signal Effectiveness</SectionTitle>
                    <p className="text-sm text-gray-300 leading-relaxed">{va.asset_symbolism.trust_signal_effectiveness}</p>
                  </Card>
                )}
              </div>
            </div>
          )}

          {activeTab === 'strategy' && (
            <div className="space-y-6">
              {/* Detailed Analysis */}
              {va?.detailed_analysis && (
                <Card>
                  <SectionTitle icon={Lightbulb}>Detailed Visual Analysis</SectionTitle>
                  <p className="text-gray-300 leading-relaxed">{va.detailed_analysis}</p>
                </Card>
              )}

              {/* POD Scores Breakdown */}
              <Card>
                <SectionTitle icon={TrendingUp}>Points of Difference Scores</SectionTitle>
                <div className="space-y-4">
                  {product.pod_scores.map((score) => {
                    const podDef = pointsOfDifference.find(p => p.axis_id === score.axis_id);
                    return (
                      <div key={score.axis_id} className="border-b border-white/5 pb-4 last:border-0 last:pb-0">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium text-white">{podDef?.axis_name || score.axis_id}</div>
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-blue-500 rounded-full" 
                                style={{ width: `${score.score * 10}%` }}
                              />
                            </div>
                            <span className="text-sm text-gray-400 tabular-nums w-8">{score.score}/10</span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-400">{score.reasoning}</p>
                        {podDef && (
                          <p className="text-xs text-gray-500 mt-2 italic">{podDef.description}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </Card>

              {/* Visual Storytelling */}
              {va?.asset_symbolism.visual_storytelling_elements && va.asset_symbolism.visual_storytelling_elements.length > 0 && (
                <Card>
                  <SectionTitle>Visual Storytelling Elements</SectionTitle>
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
          )}
        </div>
      </div>
    </div>
  );
};

// --- Product Card ---
const ProductCard = ({ product, onClick }: { product: Product; onClick: () => void }) => (
  <div 
    onClick={onClick}
    className="group relative bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl p-4 transition-all duration-300 cursor-pointer flex flex-col h-full"
  >
    <div className="relative aspect-[3/4] mb-4 overflow-hidden rounded-lg bg-white/5">
      <img src={product.image} alt={product.name} className="w-full h-full object-contain p-2 transition-transform duration-500 group-hover:scale-105" />
      {product.visual_analysis && (
        <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-sm px-2 py-1 rounded-full text-xs text-white/80 flex items-center gap-1">
          <Eye size={12} />
          {product.visual_analysis.hierarchy_clarity_score}/10
        </div>
      )}
    </div>
    
    <div className="mt-auto">
      <div className="text-xs text-blue-300 font-medium mb-1 uppercase tracking-wide">{product.brand}</div>
      <h3 className="text-sm font-semibold text-white leading-tight mb-2 line-clamp-2">{product.name}</h3>
      
      {/* Mini palette */}
      <div className="flex gap-1 mb-2">
        {product.palette.slice(0, 4).map((color, idx) => (
          <div 
            key={idx}
            className="w-4 h-4 rounded-full border border-white/20" 
            style={{ backgroundColor: color.hex_code }} 
          />
        ))}
      </div>

      <div className="flex flex-wrap gap-1">
        {product.pop_status.filter((p) => p.has_attribute).slice(0, 2).map((p) => (
          <span key={p.pop_id} className="text-[10px] px-1.5 py-0.5 bg-green-500/20 text-green-300 rounded">
            {pointsOfParity.find(pop => pop.pop_id === p.pop_id)?.pop_name.split(' ')[0] || p.pop_id.split('_')[0]}
          </span>
        ))}
        {product.pop_status.filter((p) => p.has_attribute).length > 2 && (
          <span className="text-[10px] px-1.5 py-0.5 bg-white/5 rounded text-gray-500">
            +{product.pop_status.filter((p) => p.has_attribute).length - 2}
          </span>
        )}
      </div>
    </div>
  </div>
);

// --- Strategic Insight Card ---
const InsightCard = ({ insight }: { insight: any }) => {
  const typeColors: Record<string, string> = {
    competitive_landscape: "from-blue-500/20 to-cyan-500/20 border-blue-500/30",
    differentiation_opportunity: "from-green-500/20 to-emerald-500/20 border-green-500/30",
    visual_trend: "from-purple-500/20 to-pink-500/20 border-purple-500/30",
    positioning_gap: "from-orange-500/20 to-yellow-500/20 border-orange-500/30",
  };

  return (
    <Card className={cn("bg-gradient-to-br", typeColors[insight.insight_type] || "from-gray-500/20 to-gray-600/20")}>
      <Badge variant="outline" className="mb-3">{insight.insight_type.replace(/_/g, ' ')}</Badge>
      <h4 className="text-lg font-semibold text-white mb-2">{insight.title}</h4>
      <p className="text-sm text-gray-300 leading-relaxed mb-4">{insight.description}</p>
      <div className="flex flex-wrap gap-1">
        {insight.affected_brands.map((brand: string) => (
          <span key={brand} className="text-xs bg-white/10 px-2 py-0.5 rounded text-gray-400">{brand}</span>
        ))}
      </div>
    </Card>
  );
};

// --- Main App ---
export default function App() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Calculate Category Averages for Radar
  const categoryAverages = Object.keys(axisDescriptions).map(axisId => {
    const sum = products.reduce((acc, p) => {
      const score = p.pod_scores.find(s => s.axis_id === axisId)?.score || 0;
      return acc + score;
    }, 0);
    return {
      subject: axisDescriptions[axisId],
      A: Math.round((sum / products.length) * 10) / 10,
      fullMark: 10
    };
  });

  return (
    <div className="min-h-screen p-8 md:p-12 font-sans selection:bg-pink-500/30">
      <div className="max-w-7xl mx-auto space-y-12">
        
        {/* Header */}
        <header className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs font-medium uppercase tracking-wider">
            Competitive Benchmark 2026
          </div>
          <h1 className="text-5xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/50 capitalize">
            {categoryName}
          </h1>
          <p className="text-lg text-gray-400 max-w-3xl leading-relaxed">
            {categorySummary}
          </p>
        </header>

        {/* Global Analysis */}
        <section>
          <Card className="grid md:grid-cols-3 gap-8 items-center">
            <div className="col-span-1">
              <h2 className="text-2xl font-bold mb-4">Category Landscape</h2>
              <p className="text-gray-300 mb-6 text-sm leading-relaxed">
                Average positioning scores across all {products.length} analyzed products in the category.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-white/5 rounded-lg">
                  <div className="text-3xl font-bold text-white">{products.length}</div>
                  <div className="text-xs text-gray-500 uppercase">Products</div>
                </div>
                <div className="text-center p-3 bg-white/5 rounded-lg">
                  <div className="text-3xl font-bold text-white">{Object.keys(axisDescriptions).length}</div>
                  <div className="text-xs text-gray-500 uppercase">Axes</div>
                </div>
              </div>
            </div>
            
            <div className="col-span-2 h-[320px]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={categoryAverages}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 10]} tick={false} axisLine={false} />
                  <Radar name="Category Average" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </section>

        {/* Strategic Insights */}
        <section>
          <div className="flex items-center gap-3 mb-6">
            <Lightbulb className="text-yellow-400" size={24} />
            <h2 className="text-2xl font-bold">Strategic Insights</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {strategicInsights.map((insight, idx) => (
              <InsightCard key={idx} insight={insight} />
            ))}
          </div>
        </section>

        {/* Product Grid */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Brand Portfolio ({products.length})</h2>
            <div className="text-sm text-gray-500">Click card for deep dive</div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {products.map(product => (
              <ProductCard 
                key={product.id + product.name} 
                product={product} 
                onClick={() => setSelectedProduct(product)} 
              />
            ))}
          </div>
        </section>

      </div>

      {/* Detail Modal */}
      {selectedProduct && (
        <ProductModal 
          product={selectedProduct} 
          onClose={() => setSelectedProduct(null)} 
        />
      )}
    </div>
  );
}
