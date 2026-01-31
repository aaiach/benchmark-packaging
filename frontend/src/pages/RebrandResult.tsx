import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowLeft,
  ArrowRight,
  RefreshCw,
  Download,
  ChevronDown,
  ChevronUp,
  Sparkles,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Layers,
  Palette,
  Image as ImageIcon,
  FileText,
  Zap,
} from 'lucide-react';
import { api, API_URL } from '../api/client';
import { Spinner, Card, Footer } from '../components/atoms';

/**
 * Helper to construct full image URL using API base URL
 */
function getImageUrl(path: string | undefined | null): string | undefined {
  if (!path) return undefined;
  if (path.startsWith('http')) return path;
  return `${API_URL}${path}`;
}

/**
 * Step status badge component
 */
function StepStatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
    complete: { bg: 'bg-green-50 border-green-200', text: 'text-green-600', icon: <CheckCircle size={12} /> },
    error: { bg: 'bg-red-50 border-red-200', text: 'text-red-600', icon: <XCircle size={12} /> },
    pending: { bg: 'bg-gray-50 border-gray-200', text: 'text-gray-500', icon: <Clock size={12} /> },
    skipped: { bg: 'bg-yellow-50 border-yellow-200', text: 'text-yellow-600', icon: <Clock size={12} /> },
  };
  
  const config = statusConfig[status] || statusConfig.pending;
  
  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border ${config.bg} ${config.text} text-xs font-medium`}>
      {config.icon}
      {status}
    </div>
  );
}

/**
 * Cropped element gallery component
 */
function CroppedElementGallery({ 
  images, 
  elements,
  title 
}: { 
  images: string[]; 
  elements?: any[];
  title: string;
}) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  
  if (!images || images.length === 0) {
    return (
      <div className="text-sm text-gray-400 italic">Aucune image extraite</div>
    );
  }
  
  return (
    <div className="space-y-3">
      <div className="text-sm font-medium text-gray-600">{title} ({images.length})</div>
      <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-2">
        {images.map((imgUrl, idx) => {
          const fullUrl = getImageUrl(imgUrl);
          // Try to find matching element info
          const element = elements?.[idx];
          const label = element?.element_id || element?.id || `Element ${idx + 1}`;
          
          return (
            <div key={idx} className="relative group">
              <div 
                className="aspect-square rounded-lg overflow-hidden bg-gray-100 border border-gray-200 cursor-pointer hover:border-purple-400 hover:shadow-md transition-all"
                onClick={() => setSelectedImage(fullUrl || null)}
              >
                <img
                  src={fullUrl}
                  alt={label}
                  className="w-full h-full object-contain p-1"
                  loading="lazy"
                />
              </div>
              <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[10px] px-1 py-0.5 truncate opacity-0 group-hover:opacity-100 transition-opacity">
                {label}
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Lightbox */}
      <AnimatePresence>
        {selectedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-8"
            onClick={() => setSelectedImage(null)}
          >
            <motion.img
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              src={selectedImage}
              alt="Enlarged view"
              className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Element list component for extraction details
 */
function ElementList({ elements }: { elements: any[] }) {
  if (!elements || elements.length === 0) {
    return <div className="text-sm text-gray-400 italic">Aucun élément détecté</div>;
  }
  
  const typeColors: Record<string, string> = {
    logo: 'bg-purple-100 text-purple-700',
    text: 'bg-blue-100 text-blue-700',
    trust_mark: 'bg-green-100 text-green-700',
    product_image: 'bg-orange-100 text-orange-700',
    illustration: 'bg-pink-100 text-pink-700',
    icon: 'bg-cyan-100 text-cyan-700',
    badge: 'bg-yellow-100 text-yellow-700',
    background: 'bg-gray-100 text-gray-700',
    decorative: 'bg-gray-100 text-gray-600',
  };
  
  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {elements.map((elem, idx) => (
        <div key={idx} className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg text-sm">
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeColors[elem.element_type] || typeColors.decorative}`}>
            {elem.element_type || 'unknown'}
          </span>
          <div className="flex-1 min-w-0">
            <div className="font-medium text-gray-700 truncate">{elem.element_id || elem.id}</div>
            {elem.content && (
              <div className="text-gray-500 text-xs truncate">{elem.content}</div>
            )}
          </div>
          {elem.bounding_box && (
            <div className="text-[10px] text-gray-400 font-mono">
              [{elem.bounding_box.xmin},{elem.bounding_box.ymin}]
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/**
 * Mapping entry component
 */
function MappingList({ mappings }: { mappings: any[] }) {
  if (!mappings || mappings.length === 0) {
    return <div className="text-sm text-gray-400 italic">Aucun mapping disponible</div>;
  }
  
  const actionColors: Record<string, string> = {
    keep: 'bg-blue-100 text-blue-700 border-blue-200',
    replace: 'bg-purple-100 text-purple-700 border-purple-200',
    omit: 'bg-gray-100 text-gray-500 border-gray-200',
  };
  
  return (
    <div className="space-y-2 max-h-80 overflow-y-auto">
      {mappings.map((entry, idx) => (
        <div key={idx} className={`p-3 rounded-lg border ${actionColors[entry.action] || actionColors.keep}`}>
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium text-sm">{entry.inspiration_element_id}</span>
            <span className="text-xs font-bold uppercase">{entry.action}</span>
          </div>
          {entry.action === 'replace' && entry.replacement_content && (
            <div className="text-xs mt-1">
              <span className="text-gray-500">→</span> {entry.replacement_content}
            </div>
          )}
          {entry.styling_notes && (
            <div className="text-[10px] text-gray-500 mt-1 italic">{entry.styling_notes}</div>
          )}
        </div>
      ))}
    </div>
  );
}

/**
 * Collapsible step card component
 */
function StepCard({ 
  step, 
  stepNumber,
  defaultExpanded = false 
}: { 
  step: any; 
  stepNumber: number;
  defaultExpanded?: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  
  const stepIcons: Record<string, React.ReactNode> = {
    inspiration_extraction: <Eye size={16} />,
    source_extraction: <Layers size={16} />,
    element_mapping: <Zap size={16} />,
    image_generation: <ImageIcon size={16} />,
  };
  
  const stepTitles: Record<string, string> = {
    inspiration_extraction: 'Extraction Inspiration',
    source_extraction: 'Extraction Source',
    element_mapping: 'Mapping des Éléments',
    image_generation: 'Génération Image',
  };
  
  return (
    <Card className="overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center font-bold text-sm">
            {stepNumber}
          </div>
          <div className="flex items-center gap-2 text-gray-700">
            {stepIcons[step.step_name]}
            <span className="font-medium">{stepTitles[step.step_name] || step.step_name}</span>
          </div>
          <StepStatusBadge status={step.status} />
          {step.duration_ms && (
            <span className="text-xs text-gray-400">
              {(step.duration_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{step.output_summary}</span>
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </div>
      </button>
      
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-gray-100"
          >
            <div className="p-4 space-y-4 bg-gray-50/50">
              {/* Input summary */}
              {step.input_summary && (
                <div>
                  <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Input</div>
                  <div className="text-sm text-gray-600">{step.input_summary}</div>
                </div>
              )}
              
              {/* Error message */}
              {step.error_message && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="text-xs font-semibold text-red-600 uppercase mb-1">Erreur</div>
                  <div className="text-sm text-red-700">{step.error_message}</div>
                </div>
              )}
              
              {/* Step-specific details */}
              {step.step_name === 'inspiration_extraction' && step.details && (
                <div className="space-y-4">
                  {/* Cropped images */}
                  {step.cropped_image_urls && step.cropped_image_urls.length > 0 && (
                    <CroppedElementGallery 
                      images={step.cropped_image_urls} 
                      elements={step.details.extraction?.elements}
                      title="Éléments extraits (inspiration)"
                    />
                  )}
                  
                  {/* Element list */}
                  {step.details.extraction?.elements && (
                    <div>
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2">
                        Détails des éléments ({step.details.extraction.elements.length})
                      </div>
                      <ElementList elements={step.details.extraction.elements} />
                    </div>
                  )}
                  
                  {/* Color palette */}
                  {step.details.extraction?.color_palette && step.details.extraction.color_palette.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2 flex items-center gap-1">
                        <Palette size={12} />
                        Palette de couleurs
                      </div>
                      <div className="flex gap-2">
                        {step.details.extraction.color_palette.map((color: any, idx: number) => (
                          <div key={idx} className="flex items-center gap-1">
                            <div 
                              className="w-6 h-6 rounded border border-gray-300" 
                              style={{ backgroundColor: color.hex_code }}
                              title={color.hex_code}
                            />
                            <span className="text-xs text-gray-500">{color.hex_code}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {step.step_name === 'source_extraction' && step.details && (
                <div className="space-y-4">
                  {/* Brand info */}
                  {(step.details.extraction?.brand_name || step.details.extraction?.product_name) && (
                    <div className="flex gap-4">
                      {step.details.extraction.brand_name && (
                        <div>
                          <div className="text-xs text-gray-500">Marque</div>
                          <div className="font-medium text-gray-700">{step.details.extraction.brand_name}</div>
                        </div>
                      )}
                      {step.details.extraction.product_name && (
                        <div>
                          <div className="text-xs text-gray-500">Produit</div>
                          <div className="font-medium text-gray-700">{step.details.extraction.product_name}</div>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Cropped images */}
                  {step.cropped_image_urls && step.cropped_image_urls.length > 0 && (
                    <CroppedElementGallery 
                      images={step.cropped_image_urls} 
                      elements={step.details.extraction?.elements}
                      title="Éléments extraits (source)"
                    />
                  )}
                  
                  {/* Element list */}
                  {step.details.extraction?.elements && (
                    <div>
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2">
                        Détails des éléments ({step.details.extraction.elements.length})
                      </div>
                      <ElementList elements={step.details.extraction.elements} />
                    </div>
                  )}
                  
                  {/* Claims */}
                  {step.details.extraction?.available_claims && step.details.extraction.available_claims.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Claims détectés</div>
                      <div className="flex flex-wrap gap-1">
                        {step.details.extraction.available_claims.map((claim: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">
                            {claim}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {step.step_name === 'element_mapping' && step.details && (
                <div className="space-y-4">
                  {/* LLM Debug Info - Prompts and Response */}
                  {step.details.llm_debug && (
                    <div className="space-y-3 border-b border-gray-200 pb-4">
                      <div className="text-xs font-semibold text-purple-600 uppercase flex items-center gap-1">
                        <Zap size={12} />
                        Debug LLM ({step.details.llm_debug.model || 'Opus 4.5'})
                      </div>
                      
                      {/* System Prompt */}
                      {step.details.llm_debug.system_prompt && (
                        <details className="group">
                          <summary className="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-900">
                            System Prompt ({step.details.llm_debug.system_prompt.length} chars)
                          </summary>
                          <div className="mt-2 text-xs text-gray-600 bg-purple-50 p-3 rounded border border-purple-100 font-mono max-h-48 overflow-y-auto whitespace-pre-wrap">
                            {step.details.llm_debug.system_prompt}
                          </div>
                        </details>
                      )}
                      
                      {/* User Prompt */}
                      {step.details.llm_debug.user_prompt && (
                        <details className="group">
                          <summary className="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-900">
                            User Prompt ({step.details.llm_debug.user_prompt.length} chars)
                          </summary>
                          <div className="mt-2 text-xs text-gray-600 bg-blue-50 p-3 rounded border border-blue-100 font-mono max-h-64 overflow-y-auto whitespace-pre-wrap">
                            {step.details.llm_debug.user_prompt}
                          </div>
                        </details>
                      )}
                      
                      {/* Raw Response */}
                      {step.details.llm_debug.raw_response && (
                        <details className="group">
                          <summary className="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-900">
                            Raw LLM Response ({step.details.llm_debug.raw_response.length} chars)
                          </summary>
                          <div className="mt-2 text-xs text-gray-600 bg-green-50 p-3 rounded border border-green-100 font-mono max-h-64 overflow-y-auto whitespace-pre-wrap">
                            {step.details.llm_debug.raw_response}
                          </div>
                        </details>
                      )}
                    </div>
                  )}
                  
                  {/* Color scheme */}
                  {step.details.color_scheme && (
                    <div>
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2 flex items-center gap-1">
                        <Palette size={12} />
                        Schéma de couleurs final
                      </div>
                      <div className="flex gap-3 flex-wrap">
                        {Object.entries(step.details.color_scheme).map(([key, value]) => (
                          <div key={key} className="flex items-center gap-1">
                            <div 
                              className="w-5 h-5 rounded border border-gray-300" 
                              style={{ backgroundColor: value as string }}
                            />
                            <span className="text-xs text-gray-600">{key}: {value as string}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Composition description */}
                  {step.details.composition_description && (
                    <div>
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Description de composition</div>
                      <div className="text-sm text-gray-600 bg-white p-3 rounded border">
                        {step.details.composition_description}
                      </div>
                    </div>
                  )}
                  
                  {/* Mapping decisions */}
                  {step.details.mappings && (
                    <div>
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2">
                        Décisions de mapping ({step.details.mappings.length})
                      </div>
                      <MappingList mappings={step.details.mappings} />
                    </div>
                  )}
                </div>
              )}
              
              {step.step_name === 'image_generation' && step.details && (
                <div className="space-y-4">
                  {/* LLM Debug Info */}
                  {step.details.llm_debug && (
                    <div className="space-y-3 border-b border-gray-200 pb-4">
                      <div className="text-xs font-semibold text-purple-600 uppercase flex items-center gap-1">
                        <ImageIcon size={12} />
                        Debug Génération ({step.details.llm_debug.model || 'Gemini'})
                      </div>
                      
                      {/* Target Dimensions */}
                      {step.details.llm_debug.target_dimensions && (
                        <div className="text-xs text-gray-600">
                          <span className="font-medium">Dimensions cibles:</span> {step.details.llm_debug.target_dimensions.width}x{step.details.llm_debug.target_dimensions.height}px
                          {step.details.llm_debug.attempt && step.details.llm_debug.attempt > 1 && (
                            <span className="ml-2 text-orange-600">(Tentative {step.details.llm_debug.attempt})</span>
                          )}
                        </div>
                      )}
                      
                      {/* Input Images */}
                      {step.details.llm_debug.input_image_urls && step.details.llm_debug.input_image_urls.length > 0 && (
                        <div>
                          <div className="text-xs font-medium text-gray-600 mb-2">
                            Images envoyées au modèle ({step.details.llm_debug.input_image_urls.length})
                          </div>
                          <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 gap-1">
                            {step.details.llm_debug.input_image_urls.map((imgUrl: string, idx: number) => (
                              <div key={idx} className="aspect-square rounded overflow-hidden bg-gray-100 border border-gray-200">
                                <img
                                  src={getImageUrl(imgUrl)}
                                  alt={`Input ${idx + 1}`}
                                  className="w-full h-full object-contain"
                                  loading="lazy"
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* System Prompt */}
                      {step.details.llm_debug.system_prompt && (
                        <details className="group">
                          <summary className="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-900">
                            System Prompt ({step.details.llm_debug.system_prompt.length} chars)
                          </summary>
                          <div className="mt-2 text-xs text-gray-600 bg-purple-50 p-3 rounded border border-purple-100 font-mono max-h-48 overflow-y-auto whitespace-pre-wrap">
                            {step.details.llm_debug.system_prompt}
                          </div>
                        </details>
                      )}
                      
                      {/* Composition Text (the mapping instructions) */}
                      {step.details.llm_debug.composition_text && (
                        <details className="group">
                          <summary className="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-900">
                            Instructions de Composition ({step.details.llm_debug.composition_text.length} chars)
                          </summary>
                          <div className="mt-2 text-xs text-gray-600 bg-blue-50 p-3 rounded border border-blue-100 font-mono max-h-64 overflow-y-auto whitespace-pre-wrap">
                            {step.details.llm_debug.composition_text}
                          </div>
                        </details>
                      )}
                      
                      {/* Full Prompt */}
                      {step.details.llm_debug.full_prompt && (
                        <details className="group">
                          <summary className="cursor-pointer text-xs font-medium text-gray-600 hover:text-gray-900">
                            Prompt Complet ({step.details.llm_debug.full_prompt.length} chars)
                          </summary>
                          <div className="mt-2 text-xs text-gray-600 bg-green-50 p-3 rounded border border-green-100 font-mono max-h-64 overflow-y-auto whitespace-pre-wrap">
                            {step.details.llm_debug.full_prompt}
                          </div>
                        </details>
                      )}
                      
                      {/* Error if any */}
                      {step.details.llm_debug.error && (
                        <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                          <span className="font-medium">Erreur:</span> {step.details.llm_debug.error}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Generated image info */}
                  {step.details.generated_image && (
                    <div className="text-xs text-gray-600">
                      <span className="font-medium">Image générée:</span> {step.details.generated_image}
                    </div>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

/**
 * Rebrand result page.
 * Displays all step outputs including cropped images for debugging.
 */
export function RebrandResult() {
  const { rebrandId } = useParams<{ rebrandId: string }>();
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load result directly
  useEffect(() => {
    if (!rebrandId) return;

    let isMounted = true;

    const fetchResult = async () => {
      try {
        const resultResponse = await api.rebrand.getResult(rebrandId);
        if (isMounted) {
          setResult(resultResponse);
          setLoading(false);
        }
      } catch (err: any) {
        if (isMounted) {
          if (err.status === 404) {
            setError('Rebrand non trouvé');
          } else if (err.status === 202) {
            // Rebrand still in progress - redirect to progress page
            window.location.href = `/rebrand/${rebrandId}`;
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
  }, [rebrandId]);

  // No rebrand ID
  if (!rebrandId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center py-8 max-w-md bg-white/50 border-white/60">
          <div className="text-red-500 text-xl mb-4 font-bold">Aucun ID de rebrand fourni</div>
          <Link to="/rebrand">
            <button className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors">
              Nouveau rebranding
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
          <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
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
            <Link to="/rebrand">
              <button className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors">
                Nouveau rebranding
              </button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // Success - show result
  const generatedImageUrl = getImageUrl(result?.generated_image_url);
  const sourceImageUrl = getImageUrl(result?.source_image_url);
  const inspirationImageUrl = getImageUrl(result?.inspiration_image_url);
  const isComplete = result?.status === 'complete';

  return (
    <div className="min-h-screen flex flex-col font-sans bg-gradient-to-b from-gray-50 to-white">
      <div className="flex-1 p-4 md:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Back link */}
          <Link 
            to="/rebrand" 
            className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft size={16} />
            <span className="text-sm font-medium">Nouveau rebranding</span>
          </Link>

          {/* Header */}
          <header className="space-y-2">
            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-bold uppercase tracking-wider ${
              isComplete 
                ? 'bg-green-50 border-green-200 text-green-600' 
                : 'bg-yellow-50 border-yellow-200 text-yellow-600'
            }`}>
              {isComplete ? <CheckCircle size={12} /> : <Clock size={12} />}
              {isComplete ? 'Rebranding terminé' : `Statut: ${result?.status}`}
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
              Détails du Rebranding
            </h1>
            <p className="text-sm text-gray-500 font-mono">{rebrandId}</p>
          </header>

          {/* Three-Image Comparison */}
          <div className="grid md:grid-cols-3 gap-4">
            {/* Source */}
            <Card className="space-y-2 p-4">
              <div className="text-sm font-semibold text-gray-700 text-center">
                Source (Original)
              </div>
              <div className="aspect-square rounded-xl overflow-hidden bg-white border border-gray-100">
                {sourceImageUrl ? (
                  <img
                    src={sourceImageUrl}
                    alt="Source packaging"
                    className="w-full h-full object-contain p-2"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
                    Image non disponible
                  </div>
                )}
              </div>
            </Card>

            {/* Generated (Center, larger) */}
            <Card className={`space-y-2 p-4 ${generatedImageUrl ? 'md:scale-105 md:-my-2 shadow-xl border-purple-200 bg-gradient-to-b from-purple-50/50 to-pink-50/50' : ''}`}>
              <div className="text-sm font-semibold text-purple-700 text-center flex items-center justify-center gap-2">
                <Sparkles size={14} />
                Résultat Généré
              </div>
              <div className="aspect-square rounded-xl overflow-hidden bg-white border-2 border-purple-100">
                {generatedImageUrl ? (
                  <img
                    src={generatedImageUrl}
                    alt="Generated packaging"
                    className="w-full h-full object-contain p-2"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
                    {isComplete ? 'Génération échouée' : 'En attente...'}
                  </div>
                )}
              </div>
              {generatedImageUrl && (
                <a
                  href={generatedImageUrl}
                  download={`rebrand_${rebrandId}.png`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-2 text-sm text-purple-600 hover:text-purple-800 transition-colors"
                >
                  <Download size={14} />
                  Télécharger
                </a>
              )}
            </Card>

            {/* Inspiration */}
            <Card className="space-y-2 p-4">
              <div className="text-sm font-semibold text-gray-700 text-center">
                Inspiration (Référence)
              </div>
              <div className="aspect-square rounded-xl overflow-hidden bg-white border border-gray-100">
                {inspirationImageUrl ? (
                  <img
                    src={inspirationImageUrl}
                    alt="Inspiration packaging"
                    className="w-full h-full object-contain p-2"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
                    Image non disponible
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Brand Identity */}
          {result?.brand_identity && (
            <Card className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                <FileText size={14} />
                Identité de marque & Contraintes
              </div>
              <p className="text-sm text-gray-600 whitespace-pre-line font-mono bg-gray-50 p-3 rounded-lg">
                {result.brand_identity}
              </p>
            </Card>
          )}

          {/* Pipeline Steps */}
          <div className="space-y-3">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Layers size={18} />
              Étapes du Pipeline
            </h2>
            
            {result?.steps && result.steps.length > 0 ? (
              result.steps.map((step: any, idx: number) => (
                <StepCard 
                  key={step.step_name || idx} 
                  step={step} 
                  stepNumber={idx + 1}
                  defaultExpanded={idx === 0 || step.status === 'error'}
                />
              ))
            ) : (
              <Card className="p-4 text-center text-gray-500">
                Aucune information de pipeline disponible
              </Card>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 justify-center pt-4">
            <Link to="/rebrand">
              <button className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg hover:shadow-purple-500/25 flex items-center gap-2">
                <Sparkles size={18} />
                Nouveau rebranding
              </button>
            </Link>
            <Link to="/analyses">
              <button className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors">
                Voir les analyses
              </button>
            </Link>
          </div>
        </div>
      </div>

      <Footer variant="light" />
    </div>
  );
}
