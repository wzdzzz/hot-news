import { useCallback, useEffect, useState } from "react";
import {
  fetchHotTopics,
  fetchLatest,
  fetchSources,
  type HotTopic,
  type PageResult,
  type SourceInfo,
} from "../api/client";

export function useLatestHot() {
  const [data, setData] = useState<Record<string, HotTopic[]>>({});
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchLatest();
      setData(res.data.data ?? {});
    } catch {
      console.error("Failed to fetch latest hot topics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 5 * 60 * 1000); // 每5分钟刷新
    return () => clearInterval(timer);
  }, [load]);

  return { data, loading, reload: load };
}

export function useHotTopics(params: {
  source?: string;
  category?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}) {
  const [items, setItems] = useState<HotTopic[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchHotTopics(params);
      const result = res.data.data as PageResult<HotTopic>;
      setItems(result.items ?? []);
      setTotal(result.total ?? 0);
    } catch {
      console.error("Failed to fetch hot topics");
    } finally {
      setLoading(false);
    }
  }, [params.source, params.category, params.keyword, params.page, params.page_size]);

  useEffect(() => {
    load();
  }, [load]);

  return { items, total, loading, reload: load };
}

export function useSources() {
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSources()
      .then((res) => setSources(res.data.data ?? []))
      .catch(() => console.error("Failed to fetch sources"))
      .finally(() => setLoading(false));
  }, []);

  return { sources, loading };
}
