import { useEffect, useState } from "react";
import {
  Table,
  Button,
  Tag,
  Typography,
  Card,
  Space,
  message,
  Popconfirm,
} from "antd";
import {
  PlayCircleOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import {
  fetchScraperStatus,
  runScraper,
  runAllScrapers,
  type ScraperStatus,
} from "../api/client";
import { SOURCE_NAMES } from "../components/HotCard";
import dayjs from "dayjs";

const { Title } = Typography;

export default function Admin() {
  const [statusMap, setStatusMap] = useState<Record<string, ScraperStatus>>({});
  const [loading, setLoading] = useState(true);
  const [runningKeys, setRunningKeys] = useState<Set<string>>(new Set());

  const loadStatus = async () => {
    setLoading(true);
    try {
      const res = await fetchScraperStatus();
      setStatusMap(res.data.data ?? {});
    } catch {
      message.error("获取状态失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    const timer = setInterval(loadStatus, 30_000);
    return () => clearInterval(timer);
  }, []);

  const handleRun = async (source: string) => {
    setRunningKeys((prev) => new Set(prev).add(source));
    try {
      await runScraper(source);
      message.success(`${SOURCE_NAMES[source] ?? source} 执行完成`);
      await loadStatus();
    } catch {
      message.error(`${SOURCE_NAMES[source] ?? source} 执行失败`);
    } finally {
      setRunningKeys((prev) => {
        const next = new Set(prev);
        next.delete(source);
        return next;
      });
    }
  };

  const handleRunAll = async () => {
    const allSources = Object.keys(statusMap);
    setRunningKeys(new Set(allSources));
    try {
      await runAllScrapers();
      message.success("全部爬虫执行完成");
      await loadStatus();
    } catch {
      message.error("批量执行失败");
    } finally {
      setRunningKeys(new Set());
    }
  };

  const dataSource = Object.entries(statusMap).map(([key, status]) => ({
    key,
    source: key,
    ...status,
  }));

  const columns = [
    {
      title: "来源",
      dataIndex: "source",
      key: "source",
      render: (source: string) => SOURCE_NAMES[source] ?? source,
    },
    {
      title: "状态",
      dataIndex: "last_status",
      key: "last_status",
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          success: "green",
          error: "red",
          pending: "default",
        };
        return <Tag color={colorMap[status] ?? "default"}>{status}</Tag>;
      },
    },
    {
      title: "上次运行",
      dataIndex: "last_run",
      key: "last_run",
      render: (val: string | null) =>
        val ? dayjs(val).format("YYYY-MM-DD HH:mm:ss") : "未运行",
    },
    {
      title: "抓取数量",
      dataIndex: "last_count",
      key: "last_count",
    },
    {
      title: "执行间隔",
      dataIndex: "interval",
      key: "interval",
      render: (val: number) => {
        if (val >= 3600) return `${val / 3600}小时`;
        return `${val / 60}分钟`;
      },
    },
    {
      title: "错误信息",
      dataIndex: "last_error",
      key: "last_error",
      ellipsis: true,
      render: (val: string | null) =>
        val ? (
          <Typography.Text type="danger" ellipsis>
            {val}
          </Typography.Text>
        ) : (
          "-"
        ),
    },
    {
      title: "操作",
      key: "action",
      render: (_: unknown, record: { source: string }) => (
        <Button
          type="link"
          icon={<PlayCircleOutlined />}
          loading={runningKeys.has(record.source)}
          onClick={() => handleRun(record.source)}
        >
          运行
        </Button>
      ),
    },
  ];

  const runAllLoading = runningKeys.size > 0;

  return (
    <div style={{ overflow: "hidden" }}>
      <Card>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 16,
          }}
        >
          <Title level={4} style={{ margin: 0 }}>
            爬虫管理
          </Title>
          <Space>
            <Button icon={<ReloadOutlined />} loading={loading} onClick={loadStatus}>
              刷新状态
            </Button>
            <Popconfirm
              title="确认运行全部爬虫？"
              description="这将依次执行所有已启用的爬虫"
              onConfirm={handleRunAll}
              overlayStyle={{ maxWidth: 300 }}
            >
              <Button type="primary" icon={<ThunderboltOutlined />} danger loading={runAllLoading}>
                运行全部
              </Button>
            </Popconfirm>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={dataSource}
          loading={loading}
          pagination={false}
          size="middle"
        />
      </Card>
    </div>
  );
}
