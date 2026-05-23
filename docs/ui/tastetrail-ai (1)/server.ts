import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI, Type } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  const ai = new GoogleGenAI({
    apiKey: process.env.GEMINI_API_KEY,
    httpOptions: {
      headers: {
        'User-Agent': 'aistudio-build',
      }
    }
  });

  // API Route for recommendations
  app.post("/api/recommendations", async (req, res) => {
    try {
      const { area, budget, cuisines, minRating, resultsCount, additionalPrefs } = req.body;

      const prompt = `Find ${resultsCount} best restaurant recommendations in ${area}.
      Budget: ${budget}
      Cuisines: ${cuisines.join(", ")}
      Minimum Rating: ${minRating}+
      Additional Preferences: ${additionalPrefs}

      Provide a summary of why these are good picks and then a list of restaurants.`;

      const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: prompt,
        config: {
          systemInstruction: "You are TasteTrail AI, a premium restaurant discovery concierge. Provide detailed, high-end recommendations with rankings, match percentages, and summaries. Format the response as JSON.",
          responseMimeType: "application/json",
          responseSchema: {
            type: Type.OBJECT,
            properties: {
              summary: { type: Type.STRING },
              recommendations: {
                type: Type.ARRAY,
                items: {
                  type: Type.OBJECT,
                  properties: {
                    rank: { type: Type.NUMBER },
                    name: { type: Type.STRING },
                    matchPercentage: { type: Type.NUMBER },
                    rating: { type: Type.NUMBER },
                    budget: { type: Type.STRING },
                    location: { type: Type.STRING },
                    cuisines: { type: Type.ARRAY, items: { type: Type.STRING } },
                    priceForTwo: { type: Type.STRING },
                    aiInsight: { type: Type.STRING }
                  },
                  required: ["rank", "name", "matchPercentage", "rating", "budget", "location", "cuisines", "priceForTwo", "aiInsight"]
                }
              }
            },
            required: ["summary", "recommendations"]
          },
        },
      });

      res.json(JSON.parse(response.text));
    } catch (error) {
      console.error("Gemini Error:", error);
      res.status(500).json({ error: "Failed to get recommendations" });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
