# TasteTrail-AI — Problem Statement & Project Context

## Project Overview

**TasteTrail-AI** is an AI-powered restaurant recommendation system inspired by Zomato. The application combines structured restaurant data with a Large Language Model (LLM) to deliver personalized, human-like dining suggestions based on user preferences.

The core idea is to filter a real-world restaurant dataset against explicit user criteria, then use an LLM to reason over the shortlist—ranking options and explaining why each recommendation fits—rather than relying on rigid rule-based sorting alone.

---

## Problem Statement

**AI-Powered Restaurant Recommendation System (Zomato Use Case)**

Build a recommendation service that intelligently suggests restaurants by merging:

- **Structured data** — location, cuisine, cost, ratings, and related fields from a public dataset
- **User preferences** — budget, cuisine, minimum rating, location, and optional constraints
- **LLM reasoning** — ranking, explanation, and optional summarization of top choices

The system should feel helpful and conversational while remaining grounded in actual restaurant records.

---

## Objective

Design and implement an application that:

1. Accepts user preferences (location, budget, cuisine, ratings, and optional extras)
2. Uses a real-world dataset of restaurants (Zomato-style data from Hugging Face)
3. Leverages an LLM to generate personalized, human-like recommendations
4. Displays clear, actionable results to the user

---

## Data Source

| Item | Detail |
|------|--------|
| **Dataset** | Zomato restaurant recommendation dataset |
| **Provider** | Hugging Face |
| **URL** | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |

**Relevant fields to extract** (non-exhaustive): restaurant name, location, cuisine, cost, rating, and other fields useful for filtering and display.

---

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract and normalize fields: restaurant name, location, cuisine, cost, rating, etc.
- Prepare data for filtering and for inclusion in LLM prompts

### 2. User Input

Collect preferences from the user:

| Preference | Examples |
|------------|----------|
| **Location** | Delhi, Bangalore |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | e.g. 4.0+ |
| **Additional** | family-friendly, quick service, etc. |

### 3. Integration Layer

- Filter restaurant records based on user input
- Build a structured subset of candidates for the LLM
- Design prompts that help the LLM reason over and rank options using both data and stated preferences

### 4. Recommendation Engine

Use the LLM to:

- **Rank** restaurants within the filtered set
- **Explain** why each recommendation matches the user’s preferences
- **Optionally summarize** the top choices for quick decision-making

### 5. Output Display

Present top recommendations in a user-friendly format. Each result should include:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation (why this pick fits the user)

---

## Success Criteria (High Level)

- Recommendations are **grounded** in dataset records (no fabricated venues)
- Filtering respects **hard constraints** (location, budget band, minimum rating, cuisine where applicable)
- LLM output adds **value beyond sorting**—clear rationale and readable summaries
- End-to-end flow is **understandable**: ingest → filter → prompt → rank/explain → display

---

## Scope Notes

This document defines the **problem and target architecture** for TasteTrail-AI. Implementation details (stack, API keys, UI framework, deployment) are left to the codebase and separate technical docs as the project evolves.
