# CoreDesk 智能客服中台 · 服务器部署与操作手册 (V3.0)

---

## 目录
1. [系统组成与架构说明](#1-系统组成与架构说明)
2. [服务器配置与环境要求](#2-服务器配置与环境要求)
3. [部署方案一：Docker & Docker Compose 容器化部署（推荐）](#3-部署方案一docker--docker-compose-容器化部署推荐)
4. [部署方案二：Linux 原生环境 Systemd 守护部署](#4-部署方案二linux-原生环境-systemd-守护部署)
5. [Nginx 反向代理与 SSL/HTTPS 安全配置](#5-nginx-反向代理与-sslhttps-安全配置)
6. [系统操作使用手册 (User Manual)](#6-系统操作使用手册-user-manual)
   - [6.1 访问进入与全局工作台总览](#61-访问进入与全局工作台总览)
   - [6.2 核心模式与权限机制 (Copilot vs Auto-Pilot)](#62-核心模式与权限机制-copilot-vs-auto-pilot)
   - [6.3 实时会话与智能应答作业流程](#63-实时会话与智能应答作业流程)
   - [6.4 客诉危机雷达与异常事件诊断卡](#64-客诉危机雷达与异常事件诊断卡)
   - [6.5 Action Agent 智能执行中台（掉单补单/流水冲正/关怀礼金）](#65-action-agent-智能执行中台掉单补单流水冲正关怀礼金)
   - [6.6 工单生命周期管理与协同结案](#66-工单生命周期管理与协同结案)
   - [6.7 Auto QA 智能质检与深度运营 BI 看板](#67-auto-qa-智能质检与深度运营-bi-看板)
   - [6.8 知识蒸馏自学习飞轮与影子评测沙箱](#68-知识蒸馏自学习飞轮与影子评测沙箱)
7. [日常运维与常见问题排查 (FAQ)](#7-日常运维与常见问题排查-faq)

---

## 1. 系统组成与架构说明

CoreDesk 是面向高并发与严格合规场景设计的多语言智能客服中台：
- **安全决策网关 (JEV Gateway)**：负责毫秒级意图识别、Prompt 注入与越狱拦截，并在消息输出端执行脱敏与违规承诺审核。
- **账务只读隔离 (CQRS 架构)**：直连账务中台只读镜像，提供资产、流水与打码量计算，避免写锁与并发阻塞。
- **自动分流与门禁引擎**：标准 FAQ 走自动答复；提现卡单、打码量欠额或客诉情绪等异常场景强制降级为人工作业草稿。
- **业务操作执行中台**：集成小额充值掉单免审补单 (≤¥2,000)、提现打码流水差额冲正、VIP 挽留礼金发放与反欺诈多维排查。
- **质检与知识迭代**：100% 全量会话自动打分，支持从坐席编辑差分中提炼沉淀规则并热加载入 RAG 知识库。

---

## 2. 服务器配置与环境要求

### 2.1 硬件配置建议
| 环境类型 | CPU / 内存 | 磁盘空间 | 带宽 | 建议承载量 |
|---|---|---|---|---|
| **入门/测试体验** | 1 核 / 2 GB | 20 GB SSD | 1 Mbps+ | 并发 50~100 坐席/访客 |
| **生产推荐配置** | 2 核 / 4 GB 或以上 | 50 GB SSD | 5 Mbps+ | 并发 500~2,000 会话/分钟 |
| **高并发集群** | 4 核 / 8 GB (可横向扩展) | 100 GB SSD | 10 Mbps+ | 具备 Docker 集群扩容能力 |

### 2.2 操作系统与基础软件
- **推荐操作系统**：Ubuntu 20.04 / 22.04 LTS、Debian 11 / 12、CentOS 7 / Rocky Linux 8 / 9
- **网络防火墙开放端口**：
  - `80` (HTTP - Nginx)
  - `443` (HTTPS - SSL 安全加密)
  - `8000` (FastAPI 默认内部后端端口，若使用 Nginx 代理可不对公网暴露 `8000`)

---

## 3. 部署方案一：Docker & Docker Compose 容器化部署（强烈推荐）

使用 Docker 部署具备**环境隔离**、**秒级启动**、**数据自动持久化**的优势，是最推荐的生产部署方式。

### 步骤 1：在服务器安装 Docker 与 Docker Compose
以 Ubuntu / Debian 为例：
```bash
# 更新 apt 缓存并安装基础工具
sudo apt update
sudo apt install -y curl git ca-certificates

# 安装 Docker (若未安装)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker 并设置开机自启
sudo systemctl enable --now docker

# 安装 Docker Compose 插件 (Docker 官方自带 compose-plugin)
sudo apt install -y docker-compose-plugin
```

### 步骤 2：上传/拉取项目代码至服务器
将整个项目目录上传至服务器的 `/opt/coredesk` 路径下：
```bash
# 创建部署目录并进入
sudo mkdir -p /opt/coredesk
sudo chown -R $USER:$USER /opt/coredesk
cd /opt/coredesk

# (可通过 Git 克隆或使用 scp/rsync 传输文件)
# 例: git clone <你的仓库地址> .
```

### 步骤 3：一键构建并启动容器
在项目根目录下执行：
```bash
# 构建镜像并在后台启动容器
docker compose up -d --build
```

### 步骤 4：检查容器运行状态与健康度
```bash
# 查看运行中的容器
docker compose ps

# 查看系统实时启动日志
docker compose logs -f coredesk
```
当日志输出：
```text
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```
说明容器已健康启动。

### 步骤 5：验证系统访问
在浏览器中打开：
`http://<你的服务器公网IP>:8000`
即可直接访问 CoreDesk 客服工作台。

### 常用容器运维指令：
```bash
# 停止服务
docker compose down

# 重启服务
docker compose restart

# 更新代码后重新构建启动
docker compose up -d --build
```

---

## 4. 部署方案二：Linux 原生环境 Systemd 守护部署

若服务器不方便使用 Docker，可直接使用 Python 虚拟环境配合 Linux Systemd 进行系统级守护。

### 步骤 1：安装 Python 3.11 与虚拟环境
以 Ubuntu / Debian 为例：
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

### 步骤 2：部署代码与创建虚拟环境
```bash
# 将代码放于 /opt/coredesk
sudo mkdir -p /opt/coredesk
sudo chown -R $USER:$USER /opt/coredesk
cd /opt/coredesk

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境并安装项目依赖
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

### 步骤 3：配置 Systemd 系统守护服务
项目中已预置 [coredesk.service](file:///Users/king/Documents/AIWorkSpace/Ai-customer/coredesk.service) 文件。将其安装到系统目录：
```bash
# 复制服务配置文件到 systemd
sudo cp coredesk.service /etc/systemd/system/coredesk.service

# 重载 systemd 配置
sudo systemctl daemon-reload

# 设置开机自启并立即启动服务
sudo systemctl enable --now coredesk
```

### 步骤 4：管理服务与查看日志
```bash
# 查看服务状态 (显示 active (running) 即代表成功)
sudo systemctl status coredesk

# 查看实时输出日志
sudo journalctl -u coredesk -f

# 重启服务
sudo systemctl restart coredesk

# 停止服务
sudo systemctl stop coredesk
```

---

## 5. Nginx 反向代理与 SSL/HTTPS 安全配置

生产环境中，强烈建议使用 Nginx 对外提供标准 80/443 端口服务，并配置 HTTPS 证书。

### 步骤 1：安装 Nginx
```bash
sudo apt install -y nginx
```

### 步骤 2：配置 Nginx 站点
将项目中的 [nginx/coredesk.conf](file:///Users/king/Documents/AIWorkSpace/Ai-customer/nginx/coredesk.conf) 部署至 Nginx：
```bash
sudo cp nginx/coredesk.conf /etc/nginx/conf.d/coredesk.conf

# 编辑配置文件，将 server_name 替换为您真实的域名或服务器 IP
sudo nano /etc/nginx/conf.d/coredesk.conf
```
测试配置并重载：
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 步骤 3：申请免费 Let's Encrypt SSL 证书 (推荐)
如果已解析正式域名，可使用 Certbot 一键开启 HTTPS：
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名.com
```
Certbot 将自动配置 SSL 加密与定时续期，之后可通过 `https://你的域名.com` 安全访问。

---

## 6. 全渠道即时通讯 (IM) 接入配置 (Telegram / WhatsApp / LINE)

CoreDesk 内置了统一的 IM 接入网关，支持将全球主流即时通讯工具聚合至坐席中台统一接待与回发。

### 6.1 渠道 Webhook 路由与验签标准
| 即时通讯渠道 | 服务端 Webhook 路径 | 官方协议与验签机制 | 自动回发方式 |
|---|---|---|---|
| **Telegram Bot** | `POST /api/webhook/telegram` | 校验标头 `X-Telegram-Bot-Api-Secret-Token` | `api.telegram.org/bot<TOKEN>/sendMessage` |
| **WhatsApp Cloud API** | `GET / POST /api/webhook/whatsapp` | GET 握手 `hub.verify_token`；POST 校验 `X-Hub-Signature-256` | `graph.facebook.com/v19.0/<PHONE_ID>/messages` |
| **LINE Messaging API** | `POST /api/webhook/line` | 校验标头 `X-Line-Signature` (HMAC-SHA256) | `api.line.me/v2/bot/message/reply` |

### 6.2 账号安全绑定机制 (防水平越权)
- **风控防护**：当未绑定的外部 IM 用户询问敏感资产（如提现进度、充值未到账、个人余额、流水欠额）时，系统自动阻断并提示安全码绑定，杜绝冒领与数据泄露。
- **动态指令**：用户在聊天软件内发送 `/bind <平台动态授权码>`，网关自动关联平台内部会员（如 `u1001`），后续账务只读查询无缝放行。

### 6.3 消息去重防抖 (Idempotency Filter)
Telegram 与 WhatsApp 在弱网超时后通常会自动重发相同消息。网关内置 300 秒滑动窗口幂等集合，自动比对 `(channel, message_id)`，拦截重复调度，杜绝重复回复与重复建单。

---

## 7. 完整系统使用手册 (User Manual)

### 6.1 访问进入与全局工作台总览
1. **工作台地址**：在浏览器访问 `http://<服务器IP>:8000` 或 `https://<域名>`。
2. **多语言切换**：页面右上角提供 **🇨🇳 中文 / 🇬🇧 EN / 🇻🇳 VI / 🇹🇭 TH** 切换胶囊，点击即可秒级切换全站多语言词条。
3. **主界面三栏式布局**：
   - **左侧工作区**：包含「会员画像与账务直连 CQRS 面板」、「异常事件根因诊断卡」、「快捷动作执行中台 (Action Hub)」。
   - **中央主聊天区**：包含「危机雷达指示条」、「全网主动预测广播横幅」、「消息会话气泡流」、「AI 智能草稿建议卡」与「坐席输入框」。
   - **右侧中台枢纽 (Tab 切换)**：
     - **🎫 工单中心 (Tickets Hub)**：管理异常卡单与各业务部门流转。
     - **📊 运营质检看板 (Auto QA & BI)**：查看会话打分雷达与进线诉求热力图。
     - **🔄 知识飞轮与沙箱 (Knowledge & Sandbox)**：审批坐席沉淀规则与影子评测。

---

### 6.2 核心模式与权限机制 (Copilot vs Auto-Pilot)

顶部导航栏居中位置设有**运行模式切换胶囊**：

| 模式 | 运行逻辑 | 适用场景 |
|---|---|---|
| **🧑‍💼 Copilot (坐席辅助草稿)** | 会员消息到达后，AI **仅生成回复草稿**，不直接发送给会员。坐席可审查、一键引用、一键修改后再手动点击发送。 | 新坐席上岗、大促高峰期高敏感期、风控严打期。 |
| **🤖 Auto-Pilot (智能自动驾驶)** | 会员消息到达后，经 **Risk Gating 风险引擎判定为低风险**（如标准 FAQ、基础规则、无流水欠额）时，系统在 **50ms 内秒级自主回复会员**。<br>**遇高风险（流水不足、涉诉）坚决阻断直答**，强制降级为 Copilot 草稿。 | 日常白班及夜班低人力时段，大幅降低 70%+ 的重复劳动。 |

> **抢单接管机制**：当系统处于 Auto-Pilot 模式自主回复后，气泡右上角会亮起紫靛色渐变标徽。坐席随时可以在输入框打字发送，或点击「接管此会话」，系统无缝将该会员切换为人工接管状态。

---

### 6.3 实时会话与智能应答作业流程

#### 流程 1：会员进线测试与常规咨询
1. 在中央面板底部的快捷测试按钮中，点击例如 **「模拟咨询提现流水」** 或手动在「模拟会员端进线」框输入内容发送。
2. **JEV 前置网关** 会在 1 毫秒内完成意图判别与注入拦截。
3. **CQRS 账务网关** 自动调取该会员的只读账目数据（总资产、可提余额、打码差额）。
4. **AI 事实引擎** 综合 RAG 知识库输出规范草稿：
   - 如果是 **Copilot 模式**：AI 草稿显示在输入框上方的提示卡片中。
     - 点击 **「一键采纳发送」**：直接发送给会员。
     - 点击 **「填入编辑框修改」**：草稿将填入输入框，坐席可手工增删后发送。
   - 如果是 **Auto-Pilot 模式**：
     - 无流水缺口等低风险咨询：系统自动直答并展示自主应答徽章。

---

### 6.4 客诉危机雷达与异常事件诊断卡

系统内置情感研判模型（覆盖中、英、越、泰四国语言）：
1. **P0 紧急客诉研判**：
   - 当会员输入带有强烈情绪的话术（如 *"充值两万没到账，骗子平台马上报警找媒体曝光！"*）。
   - 系统立刻触发 **P0_CRITICAL 危机预警**。
   - 顶部弹出**红色呼吸灯告警条**，提示「客诉危机预警：检测到高危客诉，建议优先安抚或转接主管」。
2. **流水缺口异常事件诊断卡**：
   - 若会员咨询提现被卡，系统会即刻在左侧展开诊断卡：
     - **实打流水**：¥45,000 / **要求流水**：¥50,000
     - **流水缺口**：¥5,000（高风险）
     - **推荐处置**：提供继续游戏打码建议，或引导使用 Phase 3 的扣除红利冲正放行。
     - 诊断卡提供 **「一键生成工单」**，秒级推送到待审核工单池。

---

### 6.5 Action Agent 智能执行中台（掉单补单/流水冲正/关怀礼金）

在左侧工作区或快捷操作栏，点击 **「智能执行中台」** 图标或对应按钮，可触发 4 大工业级业务能力：

#### 1. 小额掉单免审核验补单 (`reconcile-deposit`)
- **适用场景**：第三方渠道回调延迟或掉单。
- **操作规则**：
  - 单笔金额 **$\le ¥2,000$** 且上游存在有效流水号：系统**免审放行**，秒级完成上分冲正，记录审计单号。
  - 单笔金额 **$> ¥2,000$**：触发风险拦截，自动生成「财务大额加急对账工单」。
- **操作方式**：点击「⚡ 小额补单」-> 输入订单号与凭证 -> 点击「核验并补单」。

#### 2. 提现打码流水冲正与红利剔除 (`turnover-waiver`)
- **适用场景**：会员流水不足（如差额 ¥5,000），但同意扣除此前领取的首充优惠红利（如扣减 ¥500 红利）来免除打码要求。
- **操作方式**：点击「📉 流水冲正」-> 系统自动计算可扣减红利额 -> 坐席确认扣除 -> 系统完成提现解冻放行。

#### 3. VIP 客户关怀与挽留礼金阶梯发放 (`vip-retention`)
- **适用场景**：高价值 VIP 会员出现严重不满或流失风险。
- **额度阶梯**：
  - VIP 1~2：上限 ¥88 关怀券
  - VIP 3~5：上限 ¥288 关怀券
  - VIP 6 及以上：上限 ¥888 关怀券
- **操作方式**：点击「🎁 发放关怀券」-> 选择紧急程度 -> 自动生成券码并即刻派发至会员钱包。

#### 4. 反欺诈与黑灰产多维检测 (`anti-fraud-check`)
- 点击「🛡️ 反欺诈核查」：系统即时检测当前会员的 IP 关联度、设备指纹碰撞、同 IP 套利账号数量，返回风险置信分与处置建议（通过 / 加锁 / 限制提款）。

---

### 6.6 工单生命周期管理与协同结案

切换至右侧面板的 **「工单中心」**：
1. **状态机全生命周期**：
   - `PENDING_REVIEW`（待审核）：异常进线自动建单或坐席手动提交的待审单。
   - `IN_PROGRESS`（跟进中）：已被财务或技术排查组接单。
   - `NEED_TURNOVER`（需补足打码）：通知会员继续打码。
   - `PAYOUT_APPROVED`（审核出款）：财务审核通过并出款。
   - `RESOLVED`（已结案归档）：问题完结，归档入库。
2. **工单快捷操作**：
   - 审核出款：一键将工单状态变更为已出款，并通知前端。
   - 发放关怀券：一键派发补偿关怀券。
   - 快捷结案：填写处置备注后一键归档。

---

### 6.7 Auto QA 智能质检与深度运营 BI 看板

切换至右侧面板的 **「质检与运营看板」**：
1. **100% 全量会话五维自动质检**：
   - **礼貌态度 (20分)**、**事实准确 (30分)**、**合规底线 (25分)**、**时效推进 (15分)**、**规范完整 (10分)**。
   - 点击任一质检报告，可查看五维评分明细、**服务亮点**（如「主动使用安抚话术」）与**扣分原因**（如「未按规范使用问候语」）。
2. **运营 BI 深度洞察**：
   - 实时查看今日接待总量、Auto-Pilot 自主应答率 (如 78.4%)、平均响应时长、满意度。
   - **进线根因分布柱状图**：清晰展示提现流水缺口 (42%)、支付通道维护 (28%)、首充到账延迟 (18%)、返水计算 (12%)。
3. **全网通道主动预测广播发布**：
   - 运营人员可在此点击「发布通道预警」，如播报 *"某银行通道维护中，建议使用 USDT 极速出款"*。
   - 坐席工作台顶部即时显示跑马灯，且坐席可**一键将该广播话术引用至输入框**告知会员。

---

### 6.8 知识蒸馏自学习飞轮与影子评测沙箱

切换至右侧面板的 **「知识飞轮与沙箱」**：
1. **坐席编辑差分 (Diff) 提炼**：
   - 当坐席对 AI 给出的草稿进行了大幅度优化并发送时，系统后台会自动计算编辑距离与提炼关键句，将更优质的话术自动送入**「自学习知识蒸馏候选池」**。
2. **一键审批采纳**：
   - 知识库管理员在候选池列表中查看优化前后对比。
   - 点击 **「一键采纳沉淀」**：该话术无需重启服务，**秒级热加载**沉淀入 RAG 向量知识中台。
3. **影子评测沙箱回归 (Shadow Sandbox)**：
   - 在沙箱中输入测试问询或使用预设样本，点击「执行影子评测」。
   - 沙箱自动并发执行**基线模型 vs 候选新模型**的双路 Dual-Run 评测，输出响应延迟、JEV合规率、质检综合分并给出是否建议上线的评估结论。

---

## 7. 日常运维与常见问题排查 (FAQ)

### Q1: 部署后外网打不开，提示连接超时？
- **排查步骤**：
  1. 检查云服务器（阿里云 / 腾讯云 / AWS 等）控制台的 **安全组规则 (Security Group)**，确保放行了入方向的 `80`、`443` 或 `8000` 端口。
  2. 检查服务器系统内部防火墙：
     - Ubuntu/Debian: `sudo ufw allow 80/tcp && sudo ufw allow 8000/tcp`
     - CentOS: `sudo firewall-cmd --permanent --add-port=80/tcp && sudo firewall-cmd --reload`

### Q2: 知识库数据 `faq_knowledge.json` 存放在哪里？如何备份？
- 数据存放在 [app/data/faq_knowledge.json](file:///Users/king/Documents/AIWorkSpace/Ai-customer/app/data/faq_knowledge.json)。
- 如果使用 Docker 部署，`docker-compose.yml` 已经通过目录挂载了 `./app/data`，重启或重建容器**数据绝不会丢失**。
- 定期备份命令：
  ```bash
  tar -czvf coredesk_backup_$(date +%F).tar.gz app/data/
  ```

### Q3: 如何修改后端服务端口（比如改成 8888）？
- **Docker 方式**：修改 `docker-compose.yml` 中的端口映射：
  ```yaml
  ports:
    - "8888:8000"
  ```
- **Systemd 方式**：修改 `/etc/systemd/system/coredesk.service` 中的 `Environment="PORT=8888"`，然后执行 `sudo systemctl daemon-reload && sudo systemctl restart coredesk`。

### Q4: 如何在生产环境中查看系统报错日志？
- **Docker 部署**：
  ```bash
  docker compose logs -f --tail=200 coredesk
  ```
- **Systemd 部署**：
  ```bash
  sudo journalctl -u coredesk -f -n 200
  ```

---

> 🚀 **系统现已全面就绪，即刻根据《部署方案一 (Docker)》或《部署方案二 (Systemd)》将系统发布上线！**
