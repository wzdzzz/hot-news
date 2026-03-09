import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Table,
  Typography,
  Tag,
  Button,
  Input,
  Space,
  Breadcrumb,
  DatePicker,
} from "antd";
import {
  ArrowLeftOutlined,
  SearchOutlined,
  LinkOutlined,
} from "@ant-design/icons";
import { useHotTopics } from "../hooks/useHotData";
import { SOURCE_NAMES, CATEGORY_COLORS } from "../components/HotCard";
import type { HotTopic } from "../api/client";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

export default function SourceDetail() {
  const { source } = useParams<{ source: string }>();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [pageSize, setPageSize] = useState(30);
  const [dateRange, setDateRange] = useState<
    [Dayjs | null, Dayjs | null] | null
  >(null);

  const { items, total, loading } = useHotTopics({
    source,
    keyword: keyword || undefined,
    page,
    page_size: pageSize,
    start_date: dateRange?.[0]?.format("YYYY-MM-DD") || undefined,
    end_date: dateRange?.[1]?.format("YYYY-MM-DD") || undefined,
  });

  const columns = [
    {
      title: "排名",
      dataIndex: "rank",
      key: "rank",
      width: 70,
      render: (rank: number, _: HotTopic, index: number) => {
        const displayRank = rank || index + 1;
        const color =
          displayRank <= 3
            ? "#f5222d"
            : displayRank <= 6
              ? "#fa8c16"
              : "#999";
        return <Text strong style={{ color }}>{displayRank}</Text>;
      },
    },
    {
      title: "标题",
      dataIndex: "title",
      key: "title",
      ellipsis: true,
      render: (title: string, record: HotTopic) =>
        record.url ? (
          <a href={record.url} target="_blank" rel="noopener noreferrer">
            {title} <LinkOutlined />
          </a>
        ) : (
          title
        ),
    },
    {
      title: "热度",
      dataIndex: "hot_value",
      key: "hot_value",
      width: 120,
      render: (val: string) =>
        val ? <Tag color="red">{val}</Tag> : <Text type="secondary">-</Text>,
    },
    {
      title: "摘要",
      dataIndex: "summary",
      key: "summary",
      width: 300,
      ellipsis: true,
      render: (val: string) => (
        <Text type="secondary" ellipsis>
          {val || "-"}
        </Text>
      ),
    },
    {
      title: "爬取时间",
      dataIndex: "fetched_at",
      key: "fetched_at",
      width: 180,
      render: (val: string) =>
        val ? dayjs(val).format("YYYY-MM-DD HH:mm") : "-",
    },
  ];

  return (
    <div>
      <Breadcrumb
        items={[
          { title: <a onClick={() => navigate("/")}>热点看板</a> },
          { title: SOURCE_NAMES[source ?? ""] ?? source },
        ]}
        style={{ marginBottom: 16 }}
      />

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <Space>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate("/")}
          >
            返回
          </Button>
          <Title level={4} style={{ margin: 0 }}>
            {SOURCE_NAMES[source ?? ""] ?? source}
          </Title>
          {items[0]?.category && (
            <Tag color={CATEGORY_COLORS[items[0].category]}>
              {items[0].category}
            </Tag>
          )}
        </Space>
        <Space>
          <RangePicker
            value={dateRange}
            onChange={(dates) => {
              setDateRange(dates);
              setPage(1);
            }}
            allowClear
            placeholder={["开始日期", "结束日期"]}
          />
          <Input
            placeholder="搜索..."
            prefix={<SearchOutlined />}
            allowClear
            value={keyword}
            onChange={(e) => {
              setKeyword(e.target.value);
              setPage(1);
            }}
            style={{ width: 240 }}
          />
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={items}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          pageSizeOptions: [10, 20, 30, 50, 100],
          onChange: (p, size) => {
            if (size !== pageSize) {
              setPageSize(size);
              setPage(1);
            } else {
              setPage(p);
            }
          },
          showTotal: (t) => `共 ${t} 条`,
        }}
        size="middle"
      />
    </div>
  );
}
