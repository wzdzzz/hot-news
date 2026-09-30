import { useCallback, useEffect, useRef, useState } from "react";
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
  start_date?: string;
  end_date?: string;
}) {
  const [items, setItems] = useState<HotTopic[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  // 请求序号，丢弃乱序返回的过期响应（快速输入关键词时会连发多个请求）
  const seqRef = useRef(0);

  const load = useCallback(async () => {
    const seq = ++seqRef.current;
    setLoading(true);
    try {
      const res = await fetchHotTopics(params);
      if (seq !== seqRef.current) return;
      const result = res.data.data as PageResult<HotTopic>;
      setItems(result.items ?? []);
      setTotal(result.total ?? 0);
    } catch {
      if (seq === seqRef.current) console.error("Failed to fetch hot topics");
    } finally {
      if (seq === seqRef.current) setLoading(false);
    }
  }, [params.source, params.category, params.keyword, params.page, params.page_size, params.start_date, params.end_date]);

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
