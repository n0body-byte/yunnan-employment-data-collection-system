# 云南省企业就业失业数据采集系统

## 项目简介
本项目是一个基于 FastAPI + Vue 3 的企业就业失业数据采集与管理系统，围绕《云南省企业就业失业数据采集系统工作说明书》实现企业备案、月报填报、三级审核、数据汇总分析、通知管理、系统维护、角色权限管理和数据导出等核心业务。

系统按角色划分为三类用户：

- 省级用户：负责备案审核、报表终审、汇总分析、数据导出、系统维护、用户与角色管理
- 市级用户：负责本地区企业月报审核、通知发布
- 企业用户：负责企业备案、月度就业数据填报、历史查询、通知浏览

## 技术栈
### 后端
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL / MySQL / SQLite
- JWT 身份认证
- openpyxl
- psutil

### 前端
- Vue 3
- Vite
- Element Plus
- Axios
- ECharts

## 主要功能
### 企业端
- 企业备案信息录入与修改
- 组织机构代码、电话、邮编、邮箱等字段校验
- 行业二级联选
- 月度就业失业数据填报
- 就业人数下降时自动要求填写减少类型、主要原因和说明
- 查询本人企业历史报表及退回说明
- 浏览通知
- 修改密码

### 市级端
- 审核本地区企业月报
- 退回并填写退回原因
- 发布和删除本级通知
- 修改密码

### 省级端
- 审核企业备案
- 查询、查看、导出企业备案信息
- 月报终审、退回修改、上报部级
- 报表修订并保留修订记录
- 历史数据软删除
- 按地市汇总就业人数、岗位变动数
- 样本占比分析、对比分析、趋势分析
- 查询并导出系统账户数据
- 通知新增、修改、删除
- 上报时限设置
- 系统 CPU / 内存 / 磁盘监控
- RBAC 角色权限管理
- 国家系统数据交换日志记录

## 目录结构
```text
system/
├─ app/                     后端业务代码
│  ├─ auth.py               当前用户解析
│  ├─ config.py             配置项
│  ├─ database.py           数据库连接
│  ├─ enums.py              枚举定义
│  ├─ main.py               FastAPI 入口
│  ├─ models.py             SQLAlchemy 模型
│  ├─ routes.py             核心业务接口
│  ├─ schemas.py            Pydantic Schema
│  ├─ security.py           密码哈希与 JWT
│  └─ services/
│     └─ exporters.py       Excel 导出
├─ alembic/                 数据库迁移
├─ frontend/                Vue 3 前端
├─ scripts/                 初始化与启动脚本
├─ tests/                   测试代码
├─ submission_materials/    课程提交材料
├─ requirements.txt         后端依赖
│  ├─ seed_demo_data.py     演示数据初始化
│  └─ startup/              启动脚本
│     ├─ start_dev.bat      一键启动前后端
│     ├─ start_backend.bat  启动后端
│     ├─ start_frontend.bat 启动前端
│     └─ stop_dev.bat       关闭开发窗口
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
### 1. 创建并激活环境
如果使用 Conda：

```powershell
conda create -n yunnan-employment python=3.12 -y
conda activate yunnan-employment
```

### 2. 安装依赖
```powershell
pip install -r requirements.txt
```

### 3. 配置环境变量
复制模板文件：

```powershell
Copy-Item .env.example .env
```

常用配置项示例：

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

### 6. 启动后端服务
```powershell
uvicorn app.main:app --reload
```

启动后默认访问：

- 接口地址：`http://127.0.0.1:8000`
- OpenAPI 文档：`http://127.0.0.1:8000/docs`

## 前端安装与启动
### 1. 进入前端目录
```powershell
cd frontend
```

### 2. 安装依赖
```powershell
npm install
```

### 3. 配置前端环境变量
如需修改接口地址，可复制：

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

默认访问地址：

- `http://127.0.0.1:5173`

## 一键启动
项目根目录提供了 Windows 批处理脚本：

- `scripts/startup/start_dev.bat`：同时启动前后端
- `scripts/startup/start_backend.bat`：仅启动后端
- `scripts/startup/start_frontend.bat`：仅启动前端
- `scripts/startup/stop_dev.bat`：关闭开发窗口

如果你的 Conda 安装目录不是默认路径，需要按实际情况修改这些脚本中的 `conda.bat` 路径。

## 演示账号
初始化脚本执行后，可使用以下账号登录：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 省级用户 | `province_admin` | `Admin12345` |
| 市级用户 | `kunming_city` | `City12345` |
| 企业用户 | `demo_enterprise` | `Enterprise12345` |

登录时角色需与账号匹配：

- `province_admin` 选择 `PROVINCE`
- `kunming_city` 选择 `CITY`
- `demo_enterprise` 选择 `ENTERPRISE`

## 常用开发命令
### 运行测试
```powershell
python -m unittest tests.test_schemas tests.test_security
```

### 前端生产构建
```powershell
cd frontend
npm run build
```

### 查看数据库迁移状态
```powershell
alembic current
```

### 生成新迁移
```powershell
alembic revision --autogenerate -m "your message"
```

## 业务流程说明
### 企业备案流程
1. 省级用户创建企业账号
2. 企业用户登录后填写备案信息并提交
3. 省级用户审核备案
4. 备案通过后企业才允许填报月报

### 月报审核流程
1. 企业用户在上报时限内提交月报
2. 市级用户审核，结果为通过或退回
3. 通过后进入省级审核
4. 省级用户可终审归档、退回修改或上报部级

### 数据修订流程
1. 省级用户选择历史报表
2. 创建修订记录
3. 原始数据不直接覆盖
4. 系统保留修订日志和当前有效版本

## 权限控制说明
系统实现了基于角色的权限控制：

- 企业用户只能访问本企业备案和本企业报表
- 市级用户只能访问本地区企业和本地区月报
- 省级用户可以访问全省数据
- 除默认角色权限外，还支持省级用户创建自定义角色并分配功能权限

## 导出能力
当前系统支持导出：

- 企业备案列表 `.xlsx`
- 就业报表列表 `.xlsx`
- 用户查询结果 `.xlsx`
- 国家系统上报数据载荷

## 数据库说明
项目当前已实现 Alembic 迁移，模型包括：

- `User`
- `ManagedRole`
- `Permission`
- `Enterprise`
- `EmploymentReport`
- `EmploymentReportRevision`
- `Notification`
- `ReportingWindowConfig`
- `DataExchangeLog`

## 当前默认开发配置
如果本地使用 SQLite，数据库文件通常位于：

- [yunnan_employment.db](d:/软件工程资料/大三/下学期/软件项目管理/作业3/system/yunnan_employment.db)

如果改为 PostgreSQL 或 MySQL，请在 `.env` 中修改 `DATABASE_URL`。

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

## 注意事项
- 企业月报提交前必须先通过备案审核
- 企业月报提交必须落在已配置的上报时限内
- 省级用户可维护上报时限和系统账户
- 省级数据交换目前实现的是系统内导出与交换日志闭环，未对接外部真实国家平台接口
- 前端构建已通过，但打包体积较大，后续可继续做按路由拆包优化

## 课程提交相关
项目中已经包含课程提交材料目录：

- [submission_materials](d:/软件工程资料/大三/下学期/软件项目管理/作业3/system/submission_materials)

其中包括：

- 项目计划
- 甘特图
- 变更单
- Agent 编程系统说明
- 测试与验收说明

## 许可证
本项目当前用于课程作业与教学展示，未单独声明开源许可证。如需公开发布，建议补充 License 文件。
