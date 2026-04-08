# 云南省企业就业失业数据采集系统

## 项目简介
本项目基于 FastAPI + Vue 3 实现，面向云南省企业就业失业数据采集、审核、统计分析和系统维护场景，覆盖企业备案、月报填报、三级审核、统计图表、数据导出、用户角色管理、系统监控等核心功能。

系统按角色分为三类用户：
- 省级用户：备案审核、报表终审、统计分析、用户角色管理、系统维护、数据交换
- 市级用户：本市月报审核、通知发布、密码修改
- 企业用户：企业备案、月报填报、历史查询、通知浏览、密码修改

## 技术栈
### 后端
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL / MySQL / SQLite
- JWT
- openpyxl
- psutil

### 前端
- Vue 3
- Vite
- Element Plus
- Axios
- ECharts

## 功能清单
### 企业端
- 企业备案信息录入与修改
- 组织机构代码、电话、邮编、邮箱等字段校验
- 行业二级联选
- 月度就业失业数据填报
- 当调查期人数低于建档期人数时自动要求填写减少类型和原因
- 历史报表查询与详情查看
- 通知浏览
- 密码修改

### 市级端
- 审核本市企业月报
- 填写退回说明
- 发布和删除本级通知
- 密码修改

### 省级端
- 审核企业备案
- 报表终审、退回修改、上报部级
- 报表修订与修订记录查看
- 汇总统计、对比分析、趋势图展示
- 用户管理、角色管理、通知管理
- 上报时限配置
- 系统 CPU / 内存 / 磁盘监控
- 数据交换日志查询
- Excel 导出

## 前端界面说明
前端已完成统一后台风格重构：
- 登录页采用双栏落地页样式
- 企业、市级、省级工作台采用统一后台壳层
- 左侧导航、顶部信息栏、统计卡片、图表卡片风格统一
- 适配桌面端与移动端，窄屏下侧边栏自动切换为抽屉菜单
- 路由已做懒加载，前端构建已完成基础拆包优化

## 目录结构
```text
system/
├─ app/                         后端业务代码
│  ├─ auth.py
│  ├─ config.py
│  ├─ database.py
│  ├─ enums.py
│  ├─ main.py
│  ├─ models.py
│  ├─ routes.py
│  ├─ schemas.py
│  ├─ security.py
│  └─ services/
│     └─ exporters.py
├─ alembic/                     数据库迁移
├─ frontend/                    Vue 3 前端
├─ scripts/                     初始化与启动脚本
│  ├─ seed_demo_data.py
│  └─ startup/
│     ├─ start_dev.bat
│     ├─ start_backend.bat
│     ├─ start_frontend.bat
│     └─ stop_dev.bat
├─ submission_materials/        课程提交材料
├─ tests/                       测试代码
├─ requirements.txt             后端依赖
├─ .env.example
└─ README.md
```

## 环境要求
### 后端
- Python 3.11 及以上
- 推荐使用 Conda 或 venv

### 前端
- Node.js 18 及以上
- npm 9 及以上

### 数据库
- 开发环境可直接使用 SQLite
- 生产环境推荐 PostgreSQL 或 MySQL

## 后端安装与启动
### 1. 创建环境
```powershell
conda create -n yunnan-employment python=3.12 -y
conda activate yunnan-employment
```

### 2. 安装依赖
```powershell
pip install -r requirements.txt
```

### 3. 配置环境变量
```powershell
Copy-Item .env.example .env
```

示例：
```env
APP_TITLE=云南省企业就业失业数据采集系统
DATABASE_URL=sqlite:///./yunnan_employment.db
JWT_SECRET_KEY=replace-this-with-a-secure-key
ACCESS_TOKEN_EXPIRE_MINUTES=120
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

### 4. 执行数据库迁移
```powershell
alembic upgrade head
```

### 5. 初始化演示数据
```powershell
python scripts/seed_demo_data.py
```

### 6. 启动后端
```powershell
uvicorn app.main:app --reload
```

后端地址：
- 接口：`http://127.0.0.1:8000`
- 文档：`http://127.0.0.1:8000/docs`

## 前端安装与启动
### 1. 进入前端目录
```powershell
cd frontend
```

### 2. 安装依赖
```powershell
npm install
```

### 3. 配置环境变量
```powershell
Copy-Item .env.example .env
```

示例：
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 4. 启动前端
```powershell
npm run dev
```

前端地址：
- `http://127.0.0.1:5173`

## 一键启动
Windows 启动脚本已经统一放到 [scripts/startup](d:/软件工程资料/大三/下学期/软件项目管理/作业3/system/scripts/startup)：

- `scripts/startup/start_dev.bat`：同时启动前后端
- `scripts/startup/start_backend.bat`：仅启动后端
- `scripts/startup/start_frontend.bat`：仅启动前端
- `scripts/startup/stop_dev.bat`：关闭开发窗口

直接执行：
```powershell
.\scripts\startup\start_dev.bat
```

如果 Conda 安装路径不是默认位置，请按本机实际情况修改 `start_backend.bat` 中的 `CONDA_BAT`。

## 演示账号
初始化脚本执行后可使用以下账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 省级用户 | `province_admin` | `Admin12345` |
| 市级用户 | `kunming_city` | `City12345` |
| 企业用户 | `demo_enterprise` | `Enterprise12345` |

登录时角色需要与账号匹配：
- `province_admin` 选择 `PROVINCE`
- `kunming_city` 选择 `CITY`
- `demo_enterprise` 选择 `ENTERPRISE`

## 常用开发命令
### 运行测试
```powershell
python -m unittest tests.test_schemas tests.test_security
```

### 前端构建
```powershell
cd frontend
npm run build
```

### 查看迁移状态
```powershell
alembic current
```

### 生成新迁移
```powershell
alembic revision --autogenerate -m "your message"
```

## 业务流程
### 企业备案流程
1. 省级用户创建企业账号
2. 企业用户登录后填写备案信息并提交
3. 省级用户审核备案
4. 备案通过后企业方可填报月报

### 月报审核流程
1. 企业用户在上报时限内提交月报
2. 市级用户审核，通过或退回
3. 通过后进入省级终审
4. 省级用户可归档、退回修改或上报部级

### 数据修订流程
1. 省级用户选择历史报表
2. 创建修订记录
3. 原始数据不直接覆盖
4. 系统保留修订日志与当前有效版本

## 权限控制
系统实现了基于角色的访问控制：
- 企业用户只能访问本企业备案和本企业报表
- 市级用户只能访问本地区企业和本地区月报
- 省级用户可访问全省数据
- 省级用户可维护自定义角色并分配权限

## 导出能力
当前系统支持导出：
- 企业备案列表 `.xlsx`
- 就业报表列表 `.xlsx`
- 用户查询结果 `.xlsx`
- 国家系统上报数据载荷

## 数据库模型
当前核心模型包括：
- `User`
- `ManagedRole`
- `Permission`
- `Enterprise`
- `EmploymentReport`
- `EmploymentReportRevision`
- `Notification`
- `ReportingWindowConfig`
- `DataExchangeLog`

## 默认开发配置
本地使用 SQLite 时，数据库文件通常位于：
- [yunnan_employment.db](d:/软件工程资料/大三/下学期/软件项目管理/作业3/system/yunnan_employment.db)

如需切换到 PostgreSQL 或 MySQL，请修改 `.env` 中的 `DATABASE_URL`。

示例：
```env
DATABASE_URL=postgresql+psycopg://postgres:password@127.0.0.1:5432/yunnan_employment
```

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/yunnan_employment
```

## 已安装依赖
### 后端
来自 [requirements.txt](d:/软件工程资料/大三/下学期/软件项目管理/作业3/system/requirements.txt)：
- `fastapi`
- `uvicorn[standard]`
- `SQLAlchemy`
- `alembic`
- `psycopg[binary]`
- `PyMySQL`
- `openpyxl`
- `psutil`
- `httpx`

### 前端
来自 [frontend/package.json](d:/软件工程资料/大三/下学期/软件项目管理/作业3/system/frontend/package.json)：
- `vue`
- `vue-router`
- `element-plus`
- `axios`
- `echarts`
- `vite`
- `typescript`
- `unplugin-vue-components`
- `unplugin-auto-import`

## 课程提交说明
课程提交材料位于 [submission_materials](d:/软件工程资料/大三/下学期/软件项目管理/作业3/system/submission_materials)，包含：
- 项目计划与甘特图
- 项目计划迭代历史截图说明
- 多份项目变更单
- Agent 编程系统说明
- 测试与验收说明
- 最终提交清单
