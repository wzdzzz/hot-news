import { Card, List, Tag, Typography } from "antd";
import { FireOutlined, RiseOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import type { HotTopic } from "../api/client";

const { Text, Link } = Typography;

// 来源名称映射
const SOURCE_NAMES: Record<string, string> = {
  weibo: "微博热搜",
  baidu: "百度热搜",
  zhihu: "知乎热榜",
  sina_news: "新浪新闻",
  netease: "网易新闻",
  bbc: "BBC News",
  cnn: "CNN",
  juejin: "掘金",
  csdn: "CSDN",
  github_trending: "GitHub Trending",
  hackernews: "Hacker News",
  douyin: "抖音热榜",
  bilibili: "B站热门",
  toutiao: "今日头条",
  kr36: "36氪",
  huxiu: "虎嗅",
  sspai: "少数派",
};

const CATEGORY_COLORS: Record<string, string> = {
  social: "volcano",
  news: "blue",
  tech: "green",
  media: "purple",
};

interface Props {
  source: string;
  items: HotTopic[];
  maxShow?: number;
}

export default function HotCard({ source, items, maxShow = 10 }: Props) {
  const navigate = useNavigate();
  const displayItems = items.slice(0, maxShow);
  const category = items[0]?.category ?? "";

  return (
    <Card
      title={
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <FireOutlined style={{ color: "#f5222d" }} />
          <span>{SOURCE_NAMES[source] ?? source}</span>
          {category && (
            <Tag color={CATEGORY_COLORS[category]}>{category}</Tag>
          )}
        </div>
      }
      extra={
        <a onClick={() => navigate(`/source/${source}`)}>查看全部</a>
      }
      hoverable
      style={{ height: "100%" }}
      bodyStyle={{ padding: "8px 16px" }}
    >
      <List
        size="small"
        dataSource={displayItems}
        renderItem={(item, index) => (
          <List.Item style={{ padding: "6px 0", border: "none" }}>
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: 8,
                width: "100%",
              }}
            >
              <Text
                strong
                style={{
                  color:
                    index < 3 ? "#f5222d" : index < 6 ? "#fa8c16" : "#999",
                  minWidth: 20,
                  textAlign: "center",
                }}
              >
                {index + 1}
              </Text>
              <div style={{ flex: 1, minWidth: 0 }}>
                {item.url ? (
                  <Link
                    href={item.url}
                    target="_blank"
                    ellipsis
                    style={{ color: "#333" }}
                  >
                    {item.title}
                  </Link>
                ) : (
                  <Text ellipsis>{item.title}</Text>
                )}
              </div>
              {item.hot_value && (
                <Text type="secondary" style={{ fontSize: 12, flexShrink: 0 }}>
                  <RiseOutlined /> {item.hot_value}
                </Text>
              )}
            </div>
          </List.Item>
        )}
      />
    </Card>
  );
}

export { SOURCE_NAMES, CATEGORY_COLORS };
