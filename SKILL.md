---
name: endfield-deck
description: "用「终末地风味」的工业科技感做可照读的演示稿（PPTX / 幻灯片），主题色任意切换。支持：写一份 PPT、做一份汇报/宣讲/发布会幻灯片、要演讲稿配 PPT、把 PPT 换成红色/蓝色/品牌色、深色或浅色版式的演示文稿、slidep DSL 生成幻灯片、给 PPT 配逐页讲稿。强调色任意指定并自动做对比度校验与色板派生，含 9 种通用页型、投影可读性字号档、slidep 排版陷阱表与四步验收门禁。Use when asked to create or edit a presentation, slide deck, PPTX, keynote-style talk, or to add speaker notes to slides."
---

# endfield-deck — 任意主题色的照读演示稿

这个 skill 教你做**工业科技风的演示稿（PPTX）**：纸面加墨色、一种强调色、宽体英文配粗体中文、编号装饰、细线分区。

它的两个核心能力：

1. **主题色任意切换** —— 用户说「用红色」「用科技蓝」「用我们品牌色」，跑一条命令就得到一整套合规配色（派生色板 + 对比度实测 + 前景色决策 + 面积上限），不是手填一个 hex。
2. **一次做对** —— 沉淀了 slidep 引擎的真实排版陷阱（12 条）和一套四步验收门禁（lint 零诊断 → 逐页截图 → 像素体检 → 产物完整性）。

---

## 工作流：四步

### 第 1 步 · 读需求，定三件事

从用户的话里确定：

| 要定 | 从哪来 |
|---|---|
| **页型组合** | 封面 → 内容 → 高潮 → 收尾，各几页 |
| **强调色** | 用户指定的颜色 / 品牌色 / 主题名（"党建红""科技蓝"） |
| **有没有删除语义** | 有删除按钮、危险操作、撤销 → 红色必须保留给删除 |

页型选哪个、怎么组合，看 `references/deck-layout.md`。

### 第 2 步 · 跑色板引擎

```bash
python scripts/accent_gen.py "#A62B1F" --name 深红
```

输出：派生色板（accent / deep / soft / tint / fore）、四组 WCAG 实测、满版面积上限、语义判定、一张可直接贴进交付说明的变体卡。

**关键约束**（细节见 `references/theme-accent.md`）：
- 红色不是禁用，是**条件式**：项目无删除/危险/撤销语义时可以释放为强调色，但要写豁免
- accent 上的文字色用引擎给的 `fore`，不手写
- 派生在 HSL 空间做，RGB 混白会丢色相
- 满版铺色有面积上限，深色强调色 ≤40%，浅色 ≤15%

### 第 3 步 · 写 DSL

每个页面一个 `.slide` 文件，放 `slides/` 目录。语法见 `references/slidep-dsl.md`，版式见 `references/deck-layout.md`。

**主题色写成占位符**，不要硬编码：

```jsx
background: 'ACCENT'        // 强调色
color: 'ACCENT_FORE'         // 强调色上的文字色
background: 'ACCENT_DEEP'    // 满版底色
```

构建时统一替换，换色不用改源文件。

每页写 `notes`（第一人称逐字讲稿，120–300 字）。

### 第 4 步 · 构建 + 过门禁

```bash
# 构建（自动注入主题色、逐页 upsert、逐页截图、逐页文本校验）
python scripts/build_deck.py --slides slides/ --out deck.pptx --accent "#A62B1F" --name 深红

# 门禁 1：lint 零诊断
bash scripts/lint_deck.sh deck.pptx slides/

# 门禁 2+3：几何体检 + 像素扫描（越界、文字重叠、异常空白、强调色面积）
python scripts/scan_overflow.py --pptx deck.pptx --shots deck_shots/ --accent "#A62B1F"

# 附带：正文净字数与口播时长
python scripts/count_words.py slides/
```

**交付前必须**：lint 10/10 零诊断 + 逐页截图人工复检 + 体检报告无错误。清单见 `references/pitfalls.md`。

---

## 九种通用页型

封面 · 导语 · 要点列表 · 时间轴 · 数据看板 · 双栏对比 · 引言金句 · 高潮页 · 收尾

每种的构图、字号、禁忌见 `references/deck-layout.md`。**页型与内容和主题色解耦** —— 换题材只改内容，换主题色只改一个 hex。

---

## 硬规则（不能改）

1. **一种强调色，只做填充** —— 编号块、数据徽标、分隔短线、按钮。不做线、不做字（浅底上作字要 4.5:1 以上）。
2. **切角 = 可点击** —— 静态 PPT 里基本不用切角，但直角是默认。
3. **宽体英文配粗体中文** —— `// SECTION TITLE` 在上，中文标题在下。
4. **编号、日期、计数都是真数据** —— 不编造。
5. **细线分区** —— 1px，不用投影、发光、渐变、圆角。
6. **红色语义闸** —— 有删除语义时红色留给删除；无删除语义时红色可释放为强调色，但要在变体卡写明豁免。
7. **英文眉标禁用 `in` / `IN`** —— slidep 解析器会把独立词 `in` 当 JS 运算符，导致折行。

---

## 文件地图

| 文件 | 内容 |
| --- | --- |
| `references/theme-accent.md` | 换色六步、语义闸、四组对比度、派生算法、面积闸、变体卡 |
| `references/deck-layout.md` | 画布网格、字号阶梯、颜色角色、页眉页脚、九种页型、通用骨架 |
| `references/slidep-dsl.md` | slidep 命令、文件组织、四个组件、支持的样式属性、占位符、字体 |
| `references/pitfalls.md` | 12 条实战陷阱（现象→根因→解法→检测）+ 四步验收门禁 |
| `scripts/accent_gen.py` | 主题色引擎：派生 + 对比度 + 语义判定 + 变体卡（`text/json/css/slidep` 五种输出） |
| `scripts/build_deck.py` | 构建：注入主题色 → 逐页 upsert（重试）→ 逐页截图 → 逐页文本校验 |
| `scripts/scan_overflow.py` | 体检：越界、文字重叠、异常空白带、强调色面积 |
| `scripts/lint_deck.sh` | 门禁：逐页 `slidep lint`，汇总 diagnostics |
| `scripts/count_words.py` | 正文净字数 + 口播时长估算 |
| `assets/tokens.deck.json` | 演示稿 token：尺寸、字号阶梯、间距、颜色角色 |
| `assets/fonts/` | Saira（拉丁）+ OFL 许可证 |
| `assets/contours/` | 等高线纹理：墨版（浅底）/ 白版（深底） |

---

## 环境要求

- **slidep**：WorkBuddy 内置的演示引擎，随应用提供。找不到时确认应用已就绪。
- **字体渲染**：需设置 `FONTCONFIG_FILE` / `FONTCONFIG_PATH` 指向 `assets/fonts.conf`。
- **Python 3.7+**，脚本零第三方依赖（`scan_overflow.py` 的像素检测需要 Pillow，缺失时自动跳过该部分）。

```bash
export PATH="$HOME/.workbuddy/binaries/node/versions/22.22.2-6:$PATH"
export FONTCONFIG_FILE="<skill 目录>/assets/fonts.conf"
export FONTCONFIG_PATH="<skill 目录>/assets/fontconfig"
```

---

## 与 endfield-ui 的关系

本 skill 继承 endfield-ui 的视觉语言（终末地风味），但做两件事：

1. **把 accent 从 4 个预设扩到任意色**，并把「红色只给删除」改成条件式；
2. **把作用域从 UI 收到演示稿**，补上 slidep DSL、版式库、陷阱表和验收门禁。

两者共享同一套固定规则（强调色只做填充、切角=可点、宽体英文配粗体中文、真数字、细线、无圆角投影渐变）。

---

## 来源与许可

视觉语言与设计规则源自 [endfield-ui-skill](https://github.com/hhikr/endfield-ui-skill)（原 skill 声明代码、模板、token 与规则可自由使用）。

Saira 字体 © 2020 The Saira Project Authors，SIL Open Font License 1.1，许可证见 `assets/fonts/Saira-OFL.txt`。

等高线纹理由原 skill 的 `draw-contours.mjs` 生成。

本 skill 的主题色引擎、版式库、陷阱表、验收脚本为新增。
