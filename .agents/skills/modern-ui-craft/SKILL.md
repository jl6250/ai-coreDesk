---
name: modern-ui-craft
description: 指导前端界面设计与 UI/UX 体验重构，强制执行 Linear/Vercel/Apple 级高质感审美、微交互动效与交互自检清单（气泡/输入岛/分页/下拉失焦/浮层/色彩体系）。
---

# Modern UI/UX Craft - 高级前端审美与交互设计规范

本 Skill 旨在确保所有前端 UI、组件开发和页面重构达到 **现代化、高质感、极具视觉冲击力与流畅交互** 的专业 SaaS 标准，坚决杜绝生硬简陋的 MVP 风格。

---

## 1. 核心设计哲学 (Aesthetic Philosophy)

1. **拒绝默认与平庸**：
   - 严禁使用生硬纯色（如纯红 `#f00`、纯蓝 `#00f`、刺眼纯黑 `#000`）。
   - 采用精致中性色阶（如 Slate / Zinc / Neutral）搭配高饱和微渐变（如 Indigo 600 -> Violet 600、Emerald 500 -> Teal 500）。
2. **轻量拟物与深度层叠 (Elevation & Depth)**：
   - **双层精细边框**：外框使用 `border border-slate-200/80` (暗色下 `border-white/10`)，内部高光轮廓。
   - **柔和多重阴影**：避免单层大黑影，使用扩散柔和的氛围阴影（例如 `box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04), 0 8px 10px -6px rgba(0, 0, 0, 0.02)`）。
   - **质感玻璃拟态 (Glassmorphism)**：使用 `backdrop-blur-md bg-white/80` 或暗色 `bg-slate-900/80`，带微透明感。
3. **呼吸感与比例节奏 (Spacing & Typography)**：
   - 字体层次必须清晰：标题加粗并微缩字距（`tracking-tight font-semibold`），正文字重 `font-normal text-slate-700`，辅助字 `text-xs text-slate-400 font-medium`。
   - 避免元素贴边挤压，保留充裕的负空间与内边距。

---

## 2. 核心组件规范与黄金蓝图 (Component Blueprints)

### A. 对话气泡 (Chat Bubbles)
- **拒绝全屏满幅块状物**：单条消息严禁 `width: 100%`，必须使用 `inline-block max-w-[80%] rounded-[20px]` 自适应内容。
- **差异化圆角设计**：
  - **用户消息**：右下角平直或小圆角（如 `rounded-br-sm`），采用微渐变主色（Indigo 到 Violet）。
  - **客服/AI 消息**：左下角平直或小圆角（如 `rounded-bl-sm`），采用浅白灰色底，边框细密（`border border-slate-200/70`）。
- **结构化元信息**：时间戳、阅读状态、引用来源统一放在气泡下方或角落，字号 `text-[11px]`。

### B. 输入岛 / 全功能输入框 (Omnibar Island)
- **浮动胶囊/岛屿感**：外层容器具有微悬浮阴影，轻微内凹背景，聚焦时带有柔和环光（`ring-4 ring-indigo-500/10 border-indigo-500`）。
- **工具栏与状态区集成**：
  - 顶部/底部集成快捷常用语、文件上传、表情、多语言翻译标签。
  - 右下角实时字符数角标（如 `89/1000`）。
  - 发送按钮采用渐变胶囊按钮，禁用态为平滑灰化，可用态带有微缩放与发光效果。

### C. 数据表格与高密度看板 (Data Tables & Pagination)
- **表头**：半透明吸顶（Sticky Header），大写微缩微字距（`text-[11px] font-semibold tracking-wider uppercase text-slate-400`）。
- **行悬浮动效**：`hover:bg-slate-50/80 transition-colors duration-150`。
- **状态徽标 (Status Pills)**：一律采用微圆角胶囊 (`rounded-full px-2.5 py-0.5 text-xs font-semibold`)，前置带状态呼吸小圆点（`w-1.5 h-1.5 rounded-full`）。
- **分页控制条 (Pagination Controls)**：
  - 标明当前区间（`显示 1-10 共 38 条`）。
  - 动态单页条数选择器（`5 / 10 / 20 条/页`）。
  - 数字页码按钮（当前高亮页为品牌色带阴影，不可用页为灰度禁用态）。

### D. 下拉菜单与模态框 (Dropdowns & Modals)
- **失焦关闭规范 (Click-Outside Handler)**：
  - 任何下拉菜单（语言切换、客服状态、操作菜单）必须监听 `document.addEventListener('click')`。
  - 打开新下拉时必须自动关闭互斥的其他下拉菜单。
- **图片与媒体预览 (Lightbox)**：
  - 缩略图带圆角与微边框，悬浮放大（`hover:scale-105`）。
  - 预览必须提供全屏暗色遮罩（Lightbox Modal），支持 Esc 键退出或点击背景关闭。

---

## 3. 交互与微动效自检清单 (UX Polish Checklist)

在每次编写或修改 UI 代码后，强制检查以下 6 项：
1. [ ] **点击外部失焦**：点击页面空白区域时，所有浮层/下拉框是否正常隐退？
2. [ ] **操作反馈 (Micro-feedback)**：按钮点击是否有 `:active` 缩放或微小位移（`active:scale-[0.98]`）？
3. [ ] **过度状态 (Transitions)**：颜色、高度、透明度变化是否带有平滑过渡（`transition-all duration-200 ease-out`）？
4. [ ] **空状态处理 (Empty State)**：当列表无数据时，是否呈现精致图标 + 友好引导文字？
5. [ ] **异常与防御性渲染**：超长文本是否有省略 (`truncate` / `line-clamp-2`) 或自适应换行 (`break-words`)？
6. [ ] **移动端与自适应折叠**：侧边栏在小屏幕下是否有汉堡折叠或合理的抽屉式侧滑？
