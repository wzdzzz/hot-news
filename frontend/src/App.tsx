import { ConfigProvider, Layout, Menu, theme } from "antd";
import {
  FireOutlined,
  DashboardOutlined,
  HomeOutlined,
} from "@ant-design/icons";
import { Route, Routes, useNavigate, useLocation } from "react-router-dom";
import Home from "./pages/Home";
import SourceDetail from "./pages/SourceDetail";
import Admin from "./pages/Admin";
import zhCN from "antd/locale/zh_CN";
import "./globa.css";
const { Header, Content, Footer } = Layout;

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { key: "/", icon: <HomeOutlined />, label: "热点看板" },
    { key: "/admin", icon: <DashboardOutlined />, label: "爬虫管理" },
  ];

  const currentKey =
    menuItems.find((item) => item.key === location.pathname)?.key ?? "/";

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: { colorPrimary: "#f5222d" },
      }}
    >
      <Layout style={{ minHeight: "100vh" }}>
        <Header
          style={{
            position: "sticky",
            top: 0,
            zIndex: 100,
            display: "flex",
            alignItems: "center",
            padding: "0 24px",
            background: "#fff",
            borderBottom: "1px solid #f0f0f0",
          }}
        >
          <div
            style={{
              fontSize: 20,
              fontWeight: 700,
              marginRight: 40,
              cursor: "pointer",
              color: "#f5222d",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
            onClick={() => navigate("/")}
          >
            <FireOutlined />
            热点聚合
          </div>
          <Menu
            mode="horizontal"
            selectedKeys={[currentKey]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ flex: 1, border: "none" }}
          />
        </Header>
        <Content style={{ padding: "24px", background: "#f5f5f5", overflowX: "hidden" }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/source/:source" element={<SourceDetail />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </Content>
        <Footer style={{ textAlign: "center", color: "#999" }}>
          Hot News Scraper &copy; 2026 - 热点新闻聚合系统
        </Footer>
      </Layout>
    </ConfigProvider>
  );
}

export default App;
