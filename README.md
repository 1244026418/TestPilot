# TestPilot

TestPilot 是一个面向接口测试流程的 AI 辅助自动化测试平台。平台将接口资产、测试用例、自动执行、结果记录和 HTML 报告放在同一套工作流中，并支持从 OpenAPI、Swagger 和 Postman Collection 批量导入接口。

## 功能

- Vue 3 + TypeScript 中文管理端
- JWT 登录认证和管理员/普通用户角色
- 项目、接口、测试用例和执行记录管理
- OpenAPI / Swagger 文档导入
- Postman Collection 导入
- GPT 辅助生成正常、异常、边界和鉴权测试用例
- GPT 不可用时自动回退规则生成器
- 基于 requests 的接口执行与断言
- HTML 测试报告
- Docker Compose 一键启动
- GitHub Actions 自动运行后端测试和前端构建

## 技术架构

```text
Vue 3 + TypeScript + Element Plus
                 |
              /api
                 |
FastAPI + JWT + SQLAlchemy + requests
                 |
       MySQL             OpenAI API
```

## 本地开发

### 1. 配置环境变量

```powershell
Copy-Item .env.example .env
```

Linux / macOS：

```bash
cp .env.example .env
```

填写 MySQL 和可选的 OpenAI 配置：

```text
TESTPILOT_MYSQL_HOST=127.0.0.1
TESTPILOT_MYSQL_PORT=3306
TESTPILOT_MYSQL_USER=root
TESTPILOT_MYSQL_PASSWORD=your_mysql_password
TESTPILOT_MYSQL_DATABASE=testpilot

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

`.env` 已被 Git 忽略，不要把真实密钥提交到仓库。

### 2. 启动后端

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\init_mysql.py
uvicorn app.main:app --reload
```

### 3. 启动 Vue 前端

```powershell
cd frontend
npm install
npm run dev
```

开发地址：

- Vue 管理端：`http://127.0.0.1:5173`
- FastAPI 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/health`

## Docker Compose

Docker 会同时启动 MySQL 和包含 Vue 构建产物的 FastAPI 应用：

```bash
docker compose up --build
```

访问 `http://127.0.0.1:8000`。

默认情况下，容器 MySQL 映射到宿主机 `3307`，避免与本机已有的 `3306` 冲突。

关闭服务：

```bash
docker compose down
```

同时删除容器数据库卷：

```bash
docker compose down -v
```

## 运行测试

后端：

```powershell
pytest
```

前端生产构建：

```powershell
cd frontend
npm run build
```

## 核心流程

1. 注册并登录平台，第一个注册账号自动成为管理员。
2. 创建测试项目。
3. 手工录入接口，或导入 OpenAPI / Postman 文档。
4. 手工设计测试用例，或使用 GPT / 规则生成器批量生成。
5. 执行项目下的全部测试用例。
6. 查看状态码、响应断言、耗时、失败原因和 HTML 报告。

## API 分组

- `/api/auth`：认证与当前用户
- `/api/projects`：项目管理
- `/api/projects/{id}/endpoints`：接口管理
- `/api/endpoints/{id}/cases`：测试用例管理
- `/api/import`：OpenAPI 和 Postman 导入
- `/api/ai`：AI 测试用例生成
- `/api/projects/{id}/runs`：测试执行与报告
- `/demo-target`：内置演示接口

## 安全说明

- API key、数据库密码和 JWT secret 只从环境变量读取。
- 公开仓库中仅保留 `.env.example`，不包含真实凭据。
- 生产环境应使用高强度 `TESTPILOT_SECRET_KEY`，并限制数据库和应用端口的公网访问。
