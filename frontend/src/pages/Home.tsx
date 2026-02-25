import { useState, useMemo } from "react";
import { Col, Input, Row, Spin, Tabs, Empty, Select, Space } from "antd";
import {
  SearchOutlined,
  GlobalOutlined,
  CommentOutlined,
  LaptopOutlined,
  ReadOutlined,
  AppstoreOutlined,
} from "@ant-design/icons";
import HotCard from "../components/HotCard";
import { SOURCE_NAMES } from "../components/HotCard";
import { useLatestHot } from "../hooks/useHotData";

const CATEGORY_MAP: Record<string, string[]> = {
  social: ["weibo", "zhihu", "douyin", "bilibili"],
  news: ["baidu", "sina_news", "netease", "bbc", "cnn", "toutiao"],
  tech: ["juejin", "csdn", "github_trending", "hackernews"],
  media: ["kr36", "huxiu", "sspai"],
};

export default function Home() {
  const { data, loading } = useLatestHot();
  const [activeTab, setActiveTab] = useState("all");
  const [keyword, setKeyword] = useState("");
  const [selectedSources, setSelectedSources] = useState<string[]>([]);

  // 可用来源列表（基于实际数据）
  const sourceOptions = useMemo(() => {
    return Object.keys(data).map((key) => ({
      label: SOURCE_NAMES[key] ?? key,
      value: key,
    }));
  }, [data]);

  // 根据分类、来源和关键词过滤
  const filteredData = useMemo(() => {
    let sources = Object.keys(data);

    if (activeTab !== "all") {
      const allowedSources = CATEGORY_MAP[activeTab] ?? [];
      sources = sources.filter((s) => allowedSources.includes(s));
    }

    if (selectedSources.length > 0) {
      sources = sources.filter((s) => selectedSources.includes(s));
    }

    if (keyword) {
      const result: Record<string, typeof data[string]> = {};
      for (const source of sources) {
        const filtered = data[source]?.filter((item) =>
          item.title.toLowerCase().includes(keyword.toLowerCase())
        );
        if (filtered?.length) {
          result[source] = filtered;
        }
      }
      return result;
    }

    const result: Record<string, typeof data[string]> = {};
    for (const source of sources) {
      if (data[source]?.length) {
        result[source] = data[source];
      }
    }
    return result;
  }, [data, activeTab, keyword, selectedSources]);

  const tabItems = [
    { key: "all", label: "全部", icon: <AppstoreOutlined /> },
    { key: "social", label: "社交", icon: <CommentOutlined /> },
    { key: "news", label: "新闻", icon: <GlobalOutlined /> },
    { key: "tech", label: "科技", icon: <LaptopOutlined /> },
    { key: "media", label: "媒体", icon: <ReadOutlined /> },
  ];

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key);
            setSelectedSources([]);
          }}
          items={tabItems.map((t) => ({
            key: t.key,
            label: (
              <span>
                {t.icon} {t.label}
              </span>
            ),
          }))}
          style={{ marginBottom: 0 }}
          tabBarStyle={{ marginBottom: 0 }}
        />
        <Space wrap>
          <Select
            mode="multiple"
            allowClear
            placeholder="筛选来源..."
            value={selectedSources}
            onChange={setSelectedSources}
            options={sourceOptions}
            style={{ minWidth: 200 }}
            maxTagCount="responsive"
          />
          <Input
            placeholder="搜索热点..."
            prefix={<SearchOutlined />}
            allowClear
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: 200 }}
          />
        </Space>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 80 }}>
          <Spin size="large" tip="加载中..." />
        </div>
      ) : Object.keys(filteredData).length === 0 ? (
        <Empty description="暂无数据，请等待爬虫执行或手动触发" />
      ) : (
        <Row gutter={[16, 16]}>
          {Object.entries(filteredData).map(([source, items]) => (
            <Col key={source} xs={24} sm={24} md={12} lg={8} xl={8}>
              <HotCard source={source} items={items} />
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
}
