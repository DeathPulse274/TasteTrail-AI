import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
    Compass,
    Heart,
    Sparkles,
    Minus,
    Plus,
    Star,
    MapPin,
    Utensils,
    UtensilsCrossed,
    ChevronRight,
    Loader2,
} from 'lucide-react';
import { SearchFilters, RecommendationResponse, Recommendation } from './types.ts';

const budgetMap = {
    Budget: 'low',
    Medium: 'medium',
    Premium: 'high',
} as const;

const cuisineFallback = [
    'Ice Cream', 'Desserts', 'Beverages', 'Cafe', 'Italian', 'Fine Dining', 'Fast Food',
    'North Indian', 'South Indian', 'Chinese', 'Japanese', 'Mexican', 'Thai',
    'Lebanese', 'Continental', 'Bakery', 'Street Food', 'Biryani', 'Pizza', 'Burgers',
    'Sushi', 'Steakhouse', 'Vegan', 'Barbecue', 'Seafood', 'Mediterranean',
];

const areaFallback = ['Vijay Nagar', 'Saket', 'Indra Nagar', 'Cyber City', 'Greater Kailash', 'Hauz Khas'];

const DEFAULT_FILTERS: SearchFilters = {
    area: areaFallback[0],
    budget: 'Medium',
    cuisines: [],
    minRating: 4.5,
    resultsCount: 5,
    additionalPrefs: '',
};

const capitalize = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);

const RestaurantCard = ({ restaurant }: { restaurant: Recommendation; key?: React.Key }) => {
    const [showFull, setShowFull] = useState(false);
    const [hovering, setHovering] = useState(false);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5, scale: 1.02 }}
            className="glass-card rounded-2xl overflow-hidden group p-6 flex flex-col gap-4 relative"
        >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-zinc-500/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="flex justify-between items-start">
                <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold tracking-widest text-zinc-500 uppercase">Rank #{restaurant.rank}</span>
                    <h3 className="text-xl font-bold premium-gradient-text">{restaurant.name}</h3>
                </div>
                <div className="flex flex-col items-end">
                    <div className="px-2 py-1 bg-white/5 rounded-md text-[10px] font-bold text-cyan-400 border border-cyan-400/20">
                        {restaurant.matchPercentage}% MATCH
                    </div>
                    <button className="mt-2 text-zinc-500 hover:text-rose-400 transition-colors transition-all active:scale-125">
                        <Heart size={18} />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 py-3 border-y border-white/5">
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                    <Star className="text-cyan-500/60 fill-cyan-500/60" size={14} />
                    <span>{restaurant.rating ? restaurant.rating.toFixed(1) : 'N/A'}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                    <Utensils size={14} />
                    <span>{capitalize(restaurant.budget)}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                    <MapPin size={14} />
                    <span className="truncate">{restaurant.location}</span>
                </div>
                <div className="text-xs text-cyan-400 font-medium">
                    {restaurant.priceForTwo}
                </div>
            </div>

            <div className="flex flex-wrap gap-2">
                {restaurant.cuisines.length > 0 ? (
                    restaurant.cuisines.map((c) => (
                        <span key={c} className="px-2 py-1 bg-zinc-900/30 rounded text-[10px] text-zinc-400 border border-white/5">
                            {c}
                        </span>
                    ))
                ) : (
                    <span className="px-2 py-1 bg-zinc-900/30 rounded text-[10px] text-zinc-400 border border-white/5">No cuisine data</span>
                )}
            </div>

            <div
                className="bg-white/5 border border-white/10 rounded-xl p-3 mt-2 relative"
                onMouseEnter={() => setHovering(true)}
                onMouseLeave={() => setHovering(false)}
                onClick={() => setShowFull((s) => !s)}
                aria-label="AI explanation"
                role="button"
            >
                <div className="flex items-center gap-2 mb-1">
                    <Sparkles size={12} className="text-zinc-400" />
                    <span className="text-[10px] uppercase tracking-wider font-bold text-zinc-400">Why AI Picked It</span>
                </div>

                <p className={`text-xs text-zinc-300 leading-relaxed italic ${showFull ? '' : 'line-clamp-2'}`}>
                    "{restaurant.aiInsight}"
                </p>

                <div className={`absolute inset-0 p-4 rounded-lg z-50 bg-zinc-900/95 text-zinc-100 text-sm overflow-auto transition-opacity duration-150 ${hovering || showFull ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
                    <div className="mb-2 text-xs text-zinc-300">Full explanation</div>
                    <div className="whitespace-pre-wrap">{restaurant.aiInsight}</div>
                </div>
            </div>
        </motion.div>
    );
};

const Navbar = () => {
    return (
        <nav className="fixed top-0 left-0 right-0 h-20 px-8 flex items-center justify-between z-40 bg-transparent/40 backdrop-blur-md border-b border-white/5">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 accent-gradient rounded-xl flex items-center justify-center shadow-zinc-500/10 shadow-lg">
                    <UtensilsCrossed className="text-zinc-900" size={20} />
                </div>
                <span className="text-2xl font-bold tracking-tight premium-gradient-text font-display">TasteTrail <span className="text-zinc-500 font-light">AI</span></span>
            </div>
        </nav>
    );
};

export default function App() {
    const API_BASE_URL = import.meta.env.VITE_API_BASE || '/api';
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<RecommendationResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [cuisineSearch, setCuisineSearch] = useState('');
    const [showAreaDropdown, setShowAreaDropdown] = useState(false);
    const [showCuisineDropdown, setShowCuisineDropdown] = useState(false);
    const resultRef = useRef<HTMLDivElement>(null);
    const cuisineContainerRef = useRef<HTMLDivElement>(null);
    const areaContainerRef = useRef<HTMLDivElement>(null);
    const [areaOptions, setAreaOptions] = useState<string[]>(areaFallback);
    const [cuisineOptions, setCuisineOptions] = useState<string[]>(cuisineFallback);

    const formatAreaLabel = (location?: string | null) => {
        if (!location) return 'Select area';
        const s = String(location).trim();
        if (s.length === 0 || s.toLowerCase() === 'nan') return 'Select area';
        const suffix = ', bangalore';
        const lower = s.toLowerCase();
        if (lower.endsWith(suffix)) {
            return s.slice(0, s.length - suffix.length).trim();
        }
        return s;
    };
    const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (cuisineContainerRef.current && !cuisineContainerRef.current.contains(event.target as Node)) {
                setShowCuisineDropdown(false);
            }
            if (areaContainerRef.current && !areaContainerRef.current.contains(event.target as Node)) {
                setShowAreaDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    useEffect(() => {
        async function loadOptions() {
            try {
                const [locationsRes, cuisinesRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/locations?city=Bangalore`),
                    fetch(`${API_BASE_URL}/cuisines`),
                ]);

                if (locationsRes.ok) {
                    const data = await locationsRes.json();
                    if (Array.isArray(data.locations) && data.locations.length > 0) {
                        const filtered = data.locations.filter((l: any) => {
                            if (l === null || l === undefined) return false;
                            const s = String(l).trim();
                            if (s.length === 0) return false;
                            const label = formatAreaLabel(s);
                            if (!label || label.toLowerCase() === 'select area') return false;
                            if (label.toLowerCase().includes('nan')) return false;
                            return true;
                        });
                        if (filtered.length > 0) {
                            setAreaOptions(filtered);
                            setFilters((prev) => ({ ...prev, area: filtered[0] }));
                        }
                    }
                }

                if (cuisinesRes.ok) {
                    const data = await cuisinesRes.json();
                    if (Array.isArray(data.cuisines) && data.cuisines.length > 0) {
                        const filtered = data.cuisines.filter((c: any) => c !== null && c !== undefined && String(c).trim().length > 0 && String(c).toLowerCase() !== 'nan');
                        setCuisineOptions(filtered);
                    }
                }
            } catch (err) {
                console.warn('Could not load area or cuisine options from backend, using defaults.', err);
            }
        }

        loadOptions();
    }, []);

    const filteredCuisines = cuisineOptions.filter((c) =>
        c.toLowerCase().includes(cuisineSearch.toLowerCase()),
    );

    const toggleCuisine = (c: string) => {
        setFilters((prev) => ({
            ...prev,
            cuisines: prev.cuisines.includes(c)
                ? prev.cuisines.filter((item) => item !== c)
                : [...prev.cuisines, c],
        }));
    };

    const estimateMatch = (rank: number) => {
        return Math.max(70, Math.min(100, 100 - (rank - 1) * 6));
    };

    const handleGetRecommendations = async () => {
        if (!filters.area) {
            setError('Please select an area before requesting recommendations.');
            return;
        }

        setLoading(true);
        setResults(null);
        setError(null);

        try {
            const response = await fetch(`${API_BASE_URL}/recommendations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    location: filters.area,
                    budget: budgetMap[filters.budget],
                    cuisine: filters.cuisines[0] ?? null,
                    min_rating: filters.minRating,
                    additional_preferences: filters.additionalPrefs || null,
                    top_n: filters.resultsCount,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                setError(errorData?.detail || 'Backend request failed.');
                return;
            }

            const backendData = await response.json();
            const mapped: RecommendationResponse = {
                summary: backendData.summary || 'Here are the best available matches based on your preferences.',
                recommendations: (backendData.recommendations || []).map((rec: any) => ({
                    rank: rec.rank,
                    name: rec.restaurant?.name ?? 'Unknown restaurant',
                    matchPercentage: estimateMatch(rec.rank),
                    rating: rec.restaurant?.rating ?? 0,
                    budget: rec.restaurant?.budget_band ?? 'unknown',
                    location: rec.restaurant?.location ?? '',
                    cuisines: rec.restaurant?.cuisines ?? [],
                    priceForTwo: rec.restaurant?.estimated_cost ?? '—',
                    aiInsight: rec.explanation ?? 'AI explanation is not available.',
                })),
            };

            setResults(mapped);
            setTimeout(() => {
                resultRef.current?.scrollIntoView({ behavior: 'smooth' });
            }, 100);
        } catch (err) {
            console.error(err);
            setError('Unable to connect to the backend. Make sure the Python API is running.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen relative pb-20">
            <div className="food-bg" />
            <div className="glow-bg" />
            <Navbar />

            <main className="max-w-6xl mx-auto pt-32 px-4 md:px-8">
                <section className="text-center mb-16 relative">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 glass mb-6"
                    >
                        <Sparkles size={14} className="text-zinc-500 animate-pulse" />
                        <span className="text-[10px] font-bold tracking-widest text-zinc-400 uppercase">Discover the future of dining</span>
                    </motion.div>

                    <h1 className="text-7xl font-bold mb-6 tracking-tighter premium-gradient-text font-display">
                        TasteTrail <span className="text-zinc-600 font-light">AI</span>
                    </h1>
                    <p className="text-xl text-zinc-400 max-w-2xl mx-auto font-light leading-relaxed">
                        Personalized restaurant discovery powered by <span className="text-zinc-200">AI</span> and real-world dining preferences.
                    </p>

                    <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-96 h-96 bg-zinc-500/5 blur-[120px] rounded-full -z-10" />
                </section>

                <motion.section
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-card rounded-[2.5rem] p-6 md:p-10 max-w-4xl mx-auto cinematic-glow"
                >
                    <div className="grid md:grid-cols-2 gap-10">
                        <div className="flex flex-col gap-8">
                            <div className="flex flex-col gap-3">
                                <label className="text-xs font-bold uppercase tracking-widest text-zinc-500">Area</label>
                                <div className="relative" ref={areaContainerRef}>
                                    <div
                                        onClick={() => setShowAreaDropdown(!showAreaDropdown)}
                                        className="glass rounded-xl h-12 px-4 flex items-center justify-between cursor-pointer transition-all duration-300 hover:border-white/20"
                                    >
                                        <span className="text-sm font-medium">{formatAreaLabel(filters.area)}</span>
                                        <ChevronRight className={`text-zinc-500 transition-transform duration-300 ${showAreaDropdown ? 'rotate-270' : 'rotate-90'}`} size={16} />
                                    </div>

                                    <AnimatePresence>
                                        {showAreaDropdown && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: 10 }}
                                                className="absolute top-full left-0 w-full mt-2 glass rounded-xl overflow-hidden z-20 border border-white/10 shadow-2xl max-h-72 overflow-y-auto"
                                            >
                                                <div className="p-1">
                                                    {areaOptions.map((area) => (
                                                        <button
                                                            key={area}
                                                            onClick={() => {
                                                                setFilters({ ...filters, area });
                                                                setShowAreaDropdown(false);
                                                            }}
                                                            className={`w-full text-left px-4 py-2.5 rounded-lg text-sm transition-all ${filters.area === area ? 'bg-white/10 text-white font-semibold' : 'hover:bg-white/10 text-zinc-200'}`}
                                                        >
                                                            {formatAreaLabel(area)}
                                                        </button>
                                                    ))}
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            </div>

                            <div className="flex flex-col gap-3">
                                <label className="text-xs font-bold uppercase tracking-widest text-zinc-500">Budget Range</label>
                                <div className="grid grid-cols-3 gap-3">
                                    {['Budget', 'Medium', 'Premium'].map((b) => (
                                        <button
                                            key={b}
                                            onClick={() => setFilters({ ...filters, budget: b as SearchFilters['budget'] })}
                                            className={`h-12 rounded-xl text-sm font-medium transition-all duration-300 border ${filters.budget === b ? 'accent-gradient text-zinc-900 border-transparent shadow-lg shadow-cyan-500/10' : 'glass text-zinc-400 border-white/5 hover:border-white/20'}`}
                                        >
                                            {b}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="flex flex-col gap-3">
                                <label className="text-xs font-bold uppercase tracking-widest text-zinc-500">Preferred Cuisines</label>
                                <div className="relative" ref={cuisineContainerRef}>
                                    <div className="glass rounded-xl p-2 min-h-[48px] flex flex-wrap gap-2 items-center transition-all duration-300 focus-within:ring-2 ring-white/10">
                                        {filters.cuisines.length === 0 ? (
                                            <span className="px-2 py-1 bg-zinc-900/30 rounded-md text-sm text-zinc-400">All cuisines</span>
                                        ) : (
                                            <AnimatePresence mode="popLayout">
                                                {filters.cuisines.map((c) => (
                                                    <motion.button
                                                        key={c}
                                                        initial={{ scale: 0.8, opacity: 0 }}
                                                        animate={{ scale: 1, opacity: 1 }}
                                                        exit={{ scale: 0.8, opacity: 0 }}
                                                        onClick={() => toggleCuisine(c)}
                                                        className="px-2 py-1 bg-white/10 rounded-md text-[10px] font-bold text-white border border-white/10 flex items-center gap-1 hover:bg-white/20 transition-colors"
                                                    >
                                                        {c} <Plus size={10} className="rotate-45" />
                                                    </motion.button>
                                                ))}
                                            </AnimatePresence>
                                        )}
                                        <input
                                            type="text"
                                            value={cuisineSearch}
                                            placeholder="Search or select cuisines..."
                                            className="flex-1 bg-transparent border-none outline-none text-sm px-2 min-w-[120px] placeholder:text-zinc-600"
                                            onChange={(e) => {
                                                setCuisineSearch(e.target.value);
                                                setShowCuisineDropdown(true);
                                            }}
                                            onFocus={() => setShowCuisineDropdown(true)}
                                        />
                                    </div>

                                    <AnimatePresence>
                                        {showCuisineDropdown && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: 10 }}
                                                className="absolute top-full left-0 w-full mt-2 glass rounded-xl overflow-hidden z-20 max-h-48 overflow-y-auto border border-white/10 shadow-2xl"
                                            >
                                                <div className="p-2 grid grid-cols-2 gap-1">
                                                    {filteredCuisines.length > 0 ? (
                                                        filteredCuisines.map((c) => (
                                                            <button
                                                                key={c}
                                                                onClick={() => {
                                                                    toggleCuisine(c);
                                                                    setCuisineSearch('');
                                                                    setShowCuisineDropdown(false);
                                                                }}
                                                                className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs transition-all ${filters.cuisines.includes(c) ? 'bg-white/20 text-white font-semibold' : 'hover:bg-white/10 text-zinc-200'}`}
                                                            >
                                                                {c}
                                                                {filters.cuisines.includes(c) && <Star size={10} className="fill-white" />}
                                                            </button>
                                                        ))
                                                    ) : (
                                                        <div className="col-span-2 p-3 text-center text-xs text-zinc-600">No matching cuisines found</div>
                                                    )}
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            </div>
                        </div>

                        <div className="flex flex-col gap-8">
                            <div className="flex flex-col gap-3">
                                <div className="flex justify-between items-center">
                                    <label className="text-xs font-bold uppercase tracking-widest text-zinc-500">Minimum Rating</label>
                                    <span className="text-zinc-100 font-bold">{filters.minRating}★</span>
                                </div>
                                <input
                                    type="range"
                                    min="1"
                                    max="5"
                                    step="0.1"
                                    value={filters.minRating}
                                    onChange={(e) => setFilters({ ...filters, minRating: parseFloat(e.target.value) })}
                                    className="w-full h-2 bg-zinc-900/50 rounded-full appearance-none cursor-pointer accent-cyan-400"
                                />
                            </div>

                            <div className="flex flex-col gap-3">
                                <label className="text-xs font-bold uppercase tracking-widest text-zinc-500">Number of Results</label>
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={() => setFilters({ ...filters, resultsCount: Math.max(1, filters.resultsCount - 1) })}
                                        className="w-10 h-10 glass rounded-lg flex items-center justify-center hover:bg-white/10 active:scale-90 transition-all"
                                    >
                                        <Minus size={18} />
                                    </button>
                                    <span className="text-xl font-bold w-6 text-center">{filters.resultsCount}</span>
                                    <button
                                        onClick={() => setFilters({ ...filters, resultsCount: Math.min(10, filters.resultsCount + 1) })}
                                        className="w-10 h-10 glass rounded-lg flex items-center justify-center hover:bg-white/10 active:scale-90 transition-all"
                                    >
                                        <Plus size={18} />
                                    </button>
                                </div>
                            </div>

                            <div className="flex flex-col gap-3">
                                <label className="text-xs font-bold uppercase tracking-widest text-zinc-500">Additional preferences</label>
                                <textarea
                                    placeholder="Describe your perfect dining experience..."
                                    value={filters.additionalPrefs}
                                    onChange={(e) => setFilters({ ...filters, additionalPrefs: e.target.value })}
                                    className="w-full h-24 glass rounded-xl p-4 text-sm focus:ring-2 ring-white/10 outline-none resize-none placeholder:text-zinc-700"
                                />
                            </div>
                        </div>
                    </div>

                    {error && (
                        <div className="mt-6 rounded-2xl bg-rose-500/10 border border-rose-500/10 p-4 text-sm text-rose-200">
                            {error}
                        </div>
                    )}

                    <button
                        disabled={loading}
                        onClick={handleGetRecommendations}
                        className="w-full mt-12 py-5 accent-gradient border border-white/10 rounded-2xl text-lg font-bold flex items-center justify-center gap-3 hover:shadow-[0_20px_50px_rgba(255,255,255,0.1)] transition-all active:scale-[0.98] disabled:opacity-50 group text-zinc-900"
                    >
                        {loading ? (
                            <Loader2 className="animate-spin" size={24} />
                        ) : (
                            <Sparkles size={24} className="group-hover:rotate-12 transition-transform" />
                        )}
                        {loading ? 'AI Thinking...' : 'Get AI Recommendations'}
                    </button>
                </motion.section>

                <AnimatePresence>
                    {loading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="mt-20 flex flex-col items-center gap-6"
                        >
                            <div className="flex gap-4">
                                {[1, 2, 3].map((i) => (
                                    <motion.div
                                        key={i}
                                        animate={{ scale: [1, 1.1, 1], opacity: [0.3, 0.8, 0.3] }}
                                        transition={{ repeat: Infinity, duration: 1.5, delay: i * 0.2 }}
                                        className="w-3 h-3 bg-zinc-500 rounded-full blur-[1px]"
                                    />
                                ))}
                            </div>
                            <p className="text-zinc-500 animate-pulse text-sm font-medium uppercase tracking-[0.2em]">AI Concierge Analyzing Preferences</p>
                        </motion.div>
                    )}
                </AnimatePresence>

                {results && (
                    <div ref={resultRef} className="mt-24">
                        <motion.div
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="glass rounded-[2rem] p-8 mb-12 border border-white/5"
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <Sparkles className="text-zinc-500" size={20} />
                                <h2 className="text-sm font-bold uppercase tracking-widest text-zinc-400">AI Recommendation Insight</h2>
                            </div>
                            <p className="text-lg text-zinc-100 font-light leading-relaxed italic">{results.summary}</p>
                        </motion.div>

                        {results.recommendations.length === 0 ? (
                            <div className="glass rounded-[1rem] p-6 text-center text-zinc-400 border border-white/5">
                                <h3 className="text-lg font-semibold text-zinc-100 mb-2">No recommendations</h3>
                                <p className="text-sm">No restaurants matched your filters. Try adjusting area, cuisine, rating or budget.</p>
                            </div>
                        ) : (
                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {results.recommendations.map((restaurant, idx) => (
                                    <RestaurantCard key={idx} restaurant={restaurant} />
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </main>

            <div className="fixed top-1/4 -left-20 w-[500px] h-[500px] bg-zinc-600/5 blur-[120px] rounded-full pointer-events-none -z-10" />
            <div className="fixed bottom-0 -right-20 w-[600px] h-[600px] bg-zinc-500/5 blur-[120px] rounded-full pointer-events-none -z-10" />
        </div>
    );
}
