# 案例档案 · 黄旭华精神分享（10 页 · 深中国红 · 可照读）

这是本 skill 的**完整参考案例**：一次真实项目从选题到验收的全过程，以及可直接复制改写的成品骨架。

> 用途：接到新任务时，先看这个案例的**决策链**（为什么这么做），再克隆 `slides/` 作为版式起点。

---

## 一、项目事实卡

| 项 | 内容 |
|---|---|
| 题材 | 时代楷模 / 黄旭华（中国第一代核潜艇总设计师） |
| 场合 | 单位内部精神分享会 |
| 时长 | 约 12 分钟（正文净字 2231，照读语速 220–260 字/分） |
| 页数 | 10 页 |
| 强调色 | 深中国红 `#A62B1F`（deep `#7E1D14`，soft `#E18A81`，tint `#F8E5E3`，fore `#FFFFFF`） |
| 底色策略 | 浅底 8 页 + 深红高潮页 2 页（p6 深潜 / p10 追思） |
| 版式方案 | p4 采用「左红右浅」，红占 37.5% |
| 字号 | 主标 40 / 副标 28–32 / 正文 20–24 / 辅助 17–19 / 最小 16 |
| 交付物 | `黄旭华-照读PPT-红主题终稿.pptx` + `黄旭华精神分享-逐页演讲稿-红主题.docx` + `DESIGN.md` |

---

## 二、决策链（可迁移的方法，不是本项目专属）

### ① 为什么选深中国红而不是国旗红

| accent | 白字压上 | 作字压纸底 | 面积上限 | 判断 |
|---|---|---|---|---|
| `#C8102E` 国旗红 | 5.88:1 | 5.34:1 | ≤25% | 只到 AA，满版页必须全白且 ≥24px |
| **`#A62B1F` 深中国红** | **7.03:1** | **6.38:1** | **≤40%** | 唯一「块+字」都合规，可一色两用 |
| `#8C1A11` 暗红 | 9.25:1 | 8.40:1 | ≤40% | 最沉稳，但偏暗、缺透气感 |

**结论**：庄重题材要的是"能当底色、也能当文字色"的一档红 → 选 `#A62B1F`。

### ② 为什么红色可以用（语义豁免怎么写）

原 skill 的固定规则是"红色只给删除"。这条规则的**前提**是红色在项目里已有稳定含义（不可撤销）。本片是人物宣讲，**没有任何删除/危险/撤销语义**，前提不成立 → 红色可释放为强调色。

**但要留档**，交付说明里必须写：

> 红色豁免：本片无删除/危险/撤销语义，红色由 danger 语义释放为强调色；全片不出现任何红色删除类操作。一旦出现一处，红色在观众认知里的含义即刻回退到"危险"，强调色作废。

### ③ 为什么第 4 页不铺满红

用户明确要求"第四页不要全红"。三个版式实测后选 L1：

| 版式 | 红占 | 结论 |
|---|---|---|
| 左红右浅 | 37.5% | **采用**：左侧 480px 深红面板承载"30"（186px 白字），右侧 800px 纸底放引文 + 时间轴 + 照片 |
| 上红下浅 | 38% | 横向切割，重心偏上 |
| 浅底红块 | 17% | 太克制，没有高潮感 |

**通用规律**：满版铺色会稀释强调色的"醒目"含义 → 高潮页留 1–2 张，其余回纸底。

### ④ 为什么高潮页用深红而不是浅蒙层

| 方案 | 效果 | 代价 |
|---|---|---|
| 深红高潮页 | 主题感最强，照片与页面融为一体 | 需做图片染色 |
| 全浅底 | 最易读 | 冲击弱，"大片感"没了 |
| 浅蒙层 | 折中 | 整页发灰，红色主题感被稀释 |

→ 选深红，且把满版页严格控制为 2 页。

### ⑤ 字号为什么整体上抬

初版最小字号只有 14/15px，投影不可读；且各页字数失衡。整体抬到最小 16px、正文 20–24px 后，又出现 6 处溢出/重叠，逐页修：

| 页 | 症状 | 修法 |
|---|---|---|
| p2 | 1949 行标题换行压 1958 行 | 行高 66→70、主体 396→420、缩短标题 |
| p3 | 左栏需 553px 只有 418px | 精简三条说明至 1 行、主体 430→444 |
| p5 | 白卡最后一行被裁切 | 卡片 190→210、行高 1.58→1.5 |
| p6 | 题诗压页脚 | 绝对定位锚定 bottom:64 |
| p7 | "1970" 行被裁切 | 删重复句、时间轴行高 56→42 |
| p8 | 红卡正文溢出到卡外 | 两卡 178→240 |
| p9 | 说明段与列表重叠 | 卡片 404→440、去掉 `marginTop:'auto'` |

**规律**：字号上调必然带来溢出，**上调和排版修复必须同一轮做完**，不能分两轮。

### ⑥ 数字必须能被解释

"401"曾被质疑。它是"长征一号"核潜艇舷号（1974-08-01 命名，2003 退役，2016-10 进驻海军博物馆）。**结论：页面上出现的每个数字都要在考据表里有出处**，否则改成"舷号 401"并在图注补全称。

### ⑦ 不写自证性文案

初版 p1 有一句"这份 PPT 用的全部是真实照片，一张 AI 生成的都没有"。这是元信息，正式宣讲念出来突兀 → 直接删，不做"弱化保留"。

---

## 三、10 页成品清单

| 页 | 页型 | 内容要点 | 视觉 |
|---|---|---|---|
| 1 | 封面 | 此生属于祖国 · 黄旭华与「长征一号」 | 纸底 + 右侧照片 + 红编号块 |
| 2 | 导语 | 1958–1988：从一张白纸到一艘潜艇 | 纸底 + 三列对比 |
| 3 | 要点列表 | 三个关键选择 | 纸底 + 编号块 |
| 4 | 数据看板 | 30 年、99 岁 | **左红右浅**（红占 37.5%） |
| 5 | 双栏对比 | 隐姓埋名的日常 | 纸底 + 双栏 |
| 6 | 高潮页 | 深潜 · 名言 | **深红满版**（照片染红） |
| 7 | 时间轴 | 1958 → 1988 → 2016 | 纸底 + 时间轴 |
| 8 | 双栏对比 | 代价：家庭与身体 | 纸底 + 红卡 |
| 9 | 要点列表 | 回响与传承 | 纸底 + 列表 |
| 10 | 收尾 | 追思 | **深红满版**（照片染红） |

缩略图见 `shots/p01.jpg` … `shots/p10.jpg`。

---

## 四、克隆这个案例

### 方式 A：一键克隆（推荐）

```bash
# 克隆 10 页骨架到新项目，并把强调色换成你的
python scripts/clone_case.py \
  --dst "D:/my-project/slides" \
  --accent "#1E88E5" \
  --pages 10
```

脚本会做四件事：

1. 复制 `slides/*.slide` 到目标目录
2. 把源文件里的**主题色 token（`#FFFA00`）与 `'ACCENT'` 占位符**统一替换成你指定的强调色
3. 扫描 DSL 里引用的图片，列出**哪些素材你得自备**
4. 打印下一步命令（构建 → 门禁 → 体检）

### 方式 B：手工复制

直接把 `slides/*.slide` 拷到你的项目 `slides/` 目录，然后把文案、图片、强调色换掉。源文件是唯一真相源 —— **改内容只改 `.slide`，永远不要改 pptx**。

### 克隆后必做

```bash
# 1. 算色板（确认你的强调色过闸）
python scripts/accent_gen.py "#1E88E5" --name 科技蓝

# 2. 构建（自动注入主题色 + 文本校验抓静默失败）
python scripts/build_deck.py --slides slides/ --out deck.pptx --accent "#1E88E5"

# 3. 四步门禁
bash scripts/lint_deck.sh deck.pptx slides/
python scripts/scan_overflow.py --pptx deck.pptx --shots shots/ --accent "#1E88E5"
python scripts/count_words.py slides/
```

---

## 五、可直接复制的骨架片段

### 5.1 封面页骨架

```jsx
<Slide notes={`各位好，今天我分享的是……`} style={{
    width: 1280, height: 720, background: '#F4F4F2',
    flexDirection: 'column', fontFamily: 'Noto Sans SC', padding: 60,
}}>
    <Box style={{ flexDirection: 'row', alignItems: 'center', gap: 16, height: 34 }}>
        <Box style={{ width: 62, height: 30, background: 'ACCENT', flexDirection: 'row',
            alignItems: 'center', justifyContent: 'center' }}>
            <Text style={{ fontFamily: 'Saira', fontSize: 16, fontWeight: 700,
                color: 'ACCENT_FORE', letterSpacing: 1 }}>No.01</Text>
        </Box>
        <Text style={{ fontFamily: 'Saira', fontSize: 16, fontWeight: 700,
            letterSpacing: 2.6, color: '#5C5C5C' }}>// SECTION TITLE</Text>
    </Box>
    <Box style={{ width: 116, height: 6, background: 'ACCENT',
        marginTop: 22, marginBottom: 22 }} />
    <Text style={{ fontSize: 40, fontWeight: 800, color: '#161616', lineHeight: 1.2 }}>
        主标题
    </Text>
    <Text style={{ fontSize: 21, color: '#5C5C5C', marginTop: 16, lineHeight: 1.6 }}>
        副标题与一段 80–120 字的定性说明。
    </Text>
</Slide>
```

> 完整 9 种页型骨架见 `references/deck-layout.md`。

### 5.2 强调色页（左红右浅）

```jsx
<Box style={{ flexDirection: 'row', height: 480, width: 1280 }}>
    {/* 左：深色面板，占 37.5% */}
    <Box style={{ width: 480, background: 'ACCENT', padding: 48,
        alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ fontFamily: 'Saira', fontSize: 186, fontWeight: 900,
            color: '#FFFFFF', lineHeight: 1 }}>30</Text>
    </Box>
    {/* 右：纸底 800px */}
    <Box style={{ width: 800, background: '#F4F4F2', padding: 48,
        flexDirection: 'column' }}>
        ...
    </Box>
</Box>
```

### 5.3 深红高潮页

```jsx
<Slide style={{ width: 1280, height: 720, background: 'ACCENT_DEEP',
    flexDirection: 'column', fontFamily: 'Noto Sans SC', padding: 60 }}>
    <Image src="assets/hero.jpg" style={{ position: 'absolute', inset: 0,
        width: 1280, height: 720, opacity: 0.55 }} />
    <Image src="assets/contour_a_light.png" style={{ position: 'absolute',
        right: -40, bottom: -40, width: 560, height: 560, opacity: 0.16 }} />
    <Text style={{ fontSize: 46, fontWeight: 900, color: '#FFFFFF' }}>
        引文原话
    </Text>
</Slide>
```

### 5.4 变体卡（交付说明第一屏，直接抄）

```text
变体：深红（#A62B1F / neutral / standard / contours / standard / calm）
主视觉：待定（从自己的内容里来，不用模板占位）
页面类型：封面展示 + 内容阅读 + 高潮页 + 收尾
强调色只做填充；accent 上写 #FFFFFF 字；满版页用 #7E1D14
红色豁免：本片无删除/危险/撤销语义，红色由 danger 语义释放为强调色
```

---

## 六、本案例沉淀进 skill 的 13 条坑

全部在 `references/pitfalls.md`，每条都有现象/根因/解法/检测。与本案例直接相关的：

| 坑 | 教训 |
|---|---|
| 1 | 英文眉标禁用独立词 `in` / `IN`（被当 JS 运算符） |
| 2 | 相邻独立 `<Text>` 间距被放大 → 合并成一个 Text，段内用 `<br/>` |
| 3 | `marginTop:'auto'` 在溢出时把后置块顶上来压住前文 |
| 6 | `upsert-dsl` 会静默失败 → 必须做像素差分或 inspect 文本比对 |
| 13 | `inspect` 输出是 Markdown，下划线被转义 → 比对前要还原转义 |

---

## 七、素材说明

本案例的 10 页 DSL 引用了真实照片（来自中国军网、新华社等公开来源），**图片素材不随 skill 分发**（有版权与体积因素）。克隆脚本会列出缺失清单，你需要按页自行准备。

素材表与数据考据表在原项目的 `黄旭华-照读PPT/DESIGN.md`。
