export interface Recommendation {
    rank: number;
    name: string;
    matchPercentage: number;
    rating: number;
    budget: string;
    location: string;
    cuisines: string[];
    priceForTwo: string;
    aiInsight: string;
}

export interface RecommendationResponse {
    summary: string;
    recommendations: Recommendation[];
}

export interface SearchFilters {
    area: string;
    budget: 'Budget' | 'Medium' | 'Premium';
    cuisines: string[];
    minRating: number;
    resultsCount: number;
    additionalPrefs: string;
}
