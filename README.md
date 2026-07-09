# TestPilot

TestPilot 是一个 AI 辅助接口自动化测试平台，目标是打通接口测试的核心链路：

> 接口管理 -> 测试用例生成 -> 接口自动化执行 -> 测试结果落库 -> HTML 报告输出

## 技术栈

- FastAPI：后端接口与 Swagger 文档
- HTML + CSS + JavaScript：中文管理界面
- MySQL + SQLAlchemy：数据持久化
- requests：接口自动化执行
- 规则驱动 AI Case Generator：根据需求描述生成正常、异常、边界、鉴权类用例
- pytest：基础自动化测试

运行环境：Python 3.8+

## MySQL 配置

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

Linux / macOS 可以使用：

```bash
cp .env.example .env
```

打开 `.env`，把 MySQL 密码改成你 Navicat 里能正常连接的密码：

```text
TESTPILOT_MYSQL_HOST=127.0.0.1
TESTPILOT_MYSQL_PORT=3306
TESTPILOT_MYSQL_USER=root
TESTPILOT_MYSQL_PASSWORD=你的MySQL密码
TESTPILOT_MYSQL_DATABASE=testpilot
```

创建数据库：

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\init_mysql.py
```

也可以在 Navicat 里手动新建数据库：

```sql
CREATE DATABASE testpilot DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 快速启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Linux / macOS：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打开中文界面：

```text
http://127.0.0.1:8000/
```

打开 Swagger：

```text
http://127.0.0.1:8000/docs
```

健康检查：

```text
http://127.0.0.1:8000/health
```

## 演示数据

启动服务后，另开一个终端执行：

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\seed_demo.py
```

也可以直接在中文界面点击“生成演示项目”。

然后在中文界面选择项目并点击“执行项目”，或在 Swagger 里调用：

```text
POST /projects/{project_id}/runs
```

执行完成后，报告会生成在：

```text
reports/run_1.html
```

## 运行测试

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

## 核心 API

- `GET /`：中文管理界面
- `GET /dashboard/stats`：工作台统计数据
- `POST /auth/register`：注册账号
- `POST /projects`：创建测试项目
- `DELETE /projects/{project_id}`：删除测试项目
- `POST /projects/{project_id}/endpoints`：录入接口
- `DELETE /projects/{project_id}/endpoints/{endpoint_id}`：删除接口
- `POST /endpoints/{endpoint_id}/cases/generate`：根据需求描述生成并保存测试用例
- `DELETE /endpoints/{endpoint_id}/cases/{case_id}`：删除测试用例
- `POST /ai/generate-cases`：只生成测试用例草稿，不落库
- `POST /projects/{project_id}/runs`：执行项目下所有接口用例
- `GET /projects/{project_id}/runs`：查看历史执行记录
- `GET /projects/{project_id}/runs/{run_id}/report`：打开 HTML 报告

## 项目亮点

1. 不只是 CRUD，而是有测试平台闭环。
2. 有中文 Web 管理界面，支持项目、接口、用例和执行记录的日常操作。
3. 使用 MySQL 存储平台数据，贴近实际项目部署方式。
4. 覆盖接口测试、用例设计、自动执行、报告分析等核心能力。
5. 将测试设计经验沉淀成用例生成器，后续可替换为真实 LLM。
6. 内置 `/demo-target/*` 待测接口，不依赖外部服务也能演示。

## 后续可扩展

- 接入 DeepSeek/OpenAI，让模型读取接口文档后生成测试点。
- 支持 YAML/JSON 用例导入导出。
- 支持 Allure 报告。
- 支持失败用例自动生成 Bug 草稿。
- 支持 GitHub Actions 定时执行接口回归测试。
