import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

export interface HotTopic {
  id: number;
  source: string;
  category: string;
  title: string;
  url: string;
  hot_value: string;
  rank: number;
  summary: string;
  image_url: string;
  extra: Record<string, unknown>;
  fetched_at: string;
  created_at: string;
}

export interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}

export interface SourceInfo {
  source: string;
  category: string;
  total_count: number;
  last_fetched: string | null;
}

export interface ScraperStatus {
  last_run: string | null;
  last_status: string;
  last_count: number;
  last_error: string | null;
  interval: number;
}

// 热点相关
export const fetchHotTopics = (params: {
  source?: string;
  category?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}) => client.get<ApiResponse<PageResult<HotTopic>>>("/hot", { params });

export const fetchLatest = () =>
  client.get<ApiResponse<Record<string, HotTopic[]>>>("/hot/latest");

export const fetchSources = () =>
  client.get<ApiResponse<SourceInfo[]>>("/hot/sources");

export const fetchCategories = () =>
  client.get<ApiResponse<Record<string, string>>>("/hot/categories");

export const fetchTopicDetail = (id: number) =>
  client.get<ApiResponse<HotTopic>>(`/hot/${id}`);

// 爬虫管理
export const fetchScraperStatus = () =>
  client.get<ApiResponse<Record<string, ScraperStatus>>>("/scraper/status");

export const runScraper = (source: string) =>
  client.post<ApiResponse<ScraperStatus>>("/scraper/run", { source });

export const runAllScrapers = () =>
  client.post<ApiResponse<Record<string, ScraperStatus>>>("/scraper/run-all");

export default client;
