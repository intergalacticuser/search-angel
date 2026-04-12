import type {
  SearchRequest,
  SearchResponse,
  CompareResponse,
  CategorySearchResponse,
  SearchCategory,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class SearchAngelAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  async search(request: SearchRequest): Promise<SearchResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      throw new Error(`Search failed: ${res.status} ${res.statusText}`);
    }
    return res.json();
  }

  async categorySearch(
    query: string,
    category: SearchCategory,
    limit: number = 30,
    offset: number = 0,
    torMode: boolean = false
  ): Promise<CategorySearchResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/search/category`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, category, limit, offset, tor_mode: torMode }),
    });
    if (!res.ok) {
      throw new Error(`Category search failed: ${res.status}`);
    }
    return res.json();
  }

  async deepSearch(request: SearchRequest): Promise<SearchResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/search/deep`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...request, mode: "deep" }),
    });
    if (!res.ok) {
      throw new Error(`Deep search failed: ${res.status}`);
    }
    return res.json();
  }

  async compare(query: string, perspectives: number = 3): Promise<CompareResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/search/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, perspectives }),
    });
    if (!res.ok) {
      throw new Error(`Compare failed: ${res.status}`);
    }
    return res.json();
  }

  async health(): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/api/v1/health`);
    return res.json();
  }
}

export const api = new SearchAngelAPI();
