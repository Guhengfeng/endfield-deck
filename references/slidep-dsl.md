# slidep DSL 规范

`slidep` 是 WorkBuddy 内置的演示引擎（`@tencent/slidep`），把 JSX 风格的 DSL 编译成 PPTX。本篇只讲**语法与行为**，排版陷阱见 `pitfalls.md`。

---

## 一、命令

```bash
slidep create                      # 新建空白 PPTX
slidep upsert-dsl <pptx> --dsl-file <slide> --page-index <N>   # 写入/替换第 N 页（0 基）
slidep lint <pptx> --dsl-file <slide>                           # 版式诊断
slidep screenshot <pptx> --page-index <N> --out <png>           # 渲染成 PNG
slidep inspect <pptx>                                              # 导出 Markdown
```

**`lint` 的位置参数必须是 pptx 路径**，`--dsl-file` 单独传 DSL 文件，否则会解析到别的东西。

渲染依赖字体，需要设置：

```bash
export PATH="$HOME/.workbuddy/binaries/node/versions/22.22.2-6:$PATH"
export FONTCONFIG_FILE="<绝对路径>/assets/fonts.conf"
export FONTCONFIG_PATH="<绝对路径>/assets/fontconfig"
```

---

## 二、文件组织

```
项目根/
├── slides/
│   ├── 01.slide
│   ├── 02.slide
│   └── ...
├── assets/                 ← 图片目录，必须与 pptx 同级
│   ├── photo.jpg
│   └── contour_a.png
└── deck.pptx
```

**图片根目录 = PPTX 所在目录**，不是 DSL 文件所在目录。DSL 里写 `src="assets/photo.jpg"`，对应的物理路径是 `<pptx 所在目录>/assets/photo.jpg`。

一个项目一个 PPTX，每页一个 `.slide` 文件，文件名两位数字（`01.slide` … `10.slide`）。

---

## 三、组件

只有四个组件：

### `<Slide>`

整页。`notes` 属性写演讲备注，`style` 写页面级样式。

```jsx
<Slide notes={`第一人称逐字讲稿`} style={{
    width: 1280, height: 720, background: '#F4F4F2',
    flexDirection: 'column', fontFamily: 'Noto Sans SC', padding: 60,
}}>
    ...
</Slide>
```

### `<Box>`

容器。所有布局都靠它。

```jsx
<Box style={{ width: 480, height: 240, flexDirection: 'row', gap: 16,
    alignItems: 'center', justifyContent: 'center', background: '#FFFFFF',
    padding: 22, position: 'relative', overflow: 'hidden' }}>
    ...
</Box>
```

### `<Text>`

文本。可用 `<span>` 局部加粗，`<br/>` 换行。

```jsx
<Text style={{ fontFamily: 'Noto Sans SC', fontSize: 24, color: '#161616',
    lineHeight: 1.5, marginTop: 10 }}>
    这是<span style={{ fontWeight: 700 }}>加粗片段</span>，还有第二行。<br/>第三行。
</Text>
```

### `<Image>`

```jsx
<Image src="assets/photo.jpg" style={{
    width: 480, height: 430, objectFit: 'cover', objectPosition: 'center 45%',
}} />
```

---

## 四、支持的样式属性

引擎支持的是**有限集合**，写了不认识的属性会被静默忽略（不报错，但没效果）。

**布局**
`flexDirection`（row / column）· `flexWrap` · `alignItems` · `alignSelf` · `justifyContent`（flex-start / center / space-between / flex-end）· `gap` · `flexGrow` · `flexShrink` · `flexBasis` · `display`

**盒模型**
`width` · `height` · `minWidth` · `maxWidth` · `minHeight` · `maxHeight` · `margin` / `marginTop` / `marginRight` / `marginBottom` / `marginLeft` · `padding` / `paddingTop` / `paddingRight` / `paddingBottom` / `paddingLeft` · `border` / `borderTop` / `borderRight` / `borderBottom` / `borderLeft` / `borderColor` / `borderWidth` / `borderRadius`（及四角）

**定位**
`position`（relative / absolute）· `top` · `right` · `bottom` · `left` · `zIndex` · `overflow`

**视觉**
`background` · `backgroundImage` · `color` · `opacity` · `borderRadius` · `transform`

**文字**
`fontFamily` · `fontSize` · `fontWeight` · `fontStyle` · `fontVariant` · `lineHeight` · `letterSpacing` · `textAlign` · `textDecoration` · `whiteSpace` · `verticalAlign`

**图片**
`objectFit` · `objectPosition`

**单位**：一律逻辑像素（px）。`marginTop: 'auto'` 在 flex 容器里可用，但有陷阱（见 `pitfalls.md`）。

---

## 五、数据驱动：数组 + map

条目类的重复结构用数组 + `.map()`，比复制粘贴稳：

```jsx
const rows = [
    ['1949', '毕业于国立交大造船系', '以造船系第一名的成绩考入，从此投身海洋事业'],
    ['1958', '隐姓埋名投身核潜艇', '整整三十年，与家人几乎断了联系'],
];

{rows.map((row, i) => (
    <Box key={i} style={{ flexDirection: 'row', alignItems: 'center', height: 70,
        borderTop: i === 0 ? '1px solid #D9D9D6' : 'none' }}>
        <Text style={{ fontFamily: 'Saira', fontSize: 28, fontWeight: 900,
            color: '#161616', width: 84 }}>{row[0]}</Text>
        <Text style={{ fontFamily: 'Noto Sans SC', fontSize: 23, fontWeight: 700,
            color: '#161616', width: 310 }}>{row[1]}</Text>
        <Text style={{ fontFamily: 'Noto Sans SC', fontSize: 20, color: '#5C5C5C',
            width: 408, paddingLeft: 16, lineHeight: 1.42 }}>{row[2]}</Text>
    </Box>
))}
```

**关键**：定宽列（84 / 310 / 408）保证每行对齐；行高（70）必须容得下「标题换行 + 说明两行」，算错了会压行或裁切。

---

## 六、主题色占位符

DSL 里**不要硬编码主题色**，用占位符，构建时统一替换：

```jsx
background: 'ACCENT'        // 强调色（只做填充）
color: 'ACCENT_FORE'         // 强调色上的文字色
background: 'ACCENT_DEEP'    // 满版底色
background: 'ACCENT_SOFT'    // 浅底强调块
background: 'ACCENT_TINT'    // 极淡纹理
```

占位符的值由 `accent_gen.py` 给出，`build_deck.py --accent` 在构建期替换。这样换主题色不用改 DSL 源文件。

**替换只认带引号的完整字符串**（`'ACCENT'`），不要写成裸标识符。

---

## 七、字体

| 角色 | 字体 | 说明 |
|---|---|---|
| 拉丁（编号、标签、英文眉标、数字） | **Saira** | 宽体几何可变字体，`assets/fonts/` 里有 Black / Bold / Wide 静态版 |
| 中文正文 | Noto Sans SC / 思源黑体 / 系统黑体 | 不要用楷体、宋体、等宽 |

```jsx
<Text style={{ fontFamily: 'Saira', fontSize: 16, fontWeight: 700,
    letterSpacing: 2.6, color: '#5C5C5C' }}>// SECTION</Text>
```

拉丁标签全大写 + 字距 0.14em（`letterSpacing: 2.6` 对应 16px 字号）；中文不加字距。

Saira 许可证（SIL OFL 1.1）随包分发，见 `assets/fonts/Saira-OFL.txt`。

---

## 八、常用骨架片段

**页眉（编号块 + 英文眉标）**
```jsx
<Box style={{ flexDirection: 'row', alignItems: 'center', gap: 16, height: 34 }}>
    <Box style={{ width: 62, height: 30, background: 'ACCENT', flexDirection: 'row',
        alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ fontFamily: 'Saira', fontSize: 16, fontWeight: 700,
            color: 'ACCENT_FORE', letterSpacing: 1 }}>No.01</Text>
    </Box>
    <Text style={{ fontFamily: 'Saira', fontSize: 16, fontWeight: 700,
        letterSpacing: 2.6, color: '#5C5C5C' }}>// SECTION TITLE</Text>
</Box>
```

**图片 + 底部图注条**
```jsx
<Box style={{ width: 480, height: 444, position: 'relative', overflow: 'hidden',
    background: '#E4E4E0' }}>
    <Image src="assets/photo.jpg" style={{ width: 480, height: 444,
        objectFit: 'cover', objectPosition: 'center 45%' }} />
    <Box style={{ position: 'absolute', left: 0, bottom: 0, right: 0, height: 50,
        background: '#161616', flexDirection: 'row', alignItems: 'center',
        paddingLeft: 16, paddingRight: 16 }}>
        <Text style={{ fontFamily: 'Saira', fontSize: 16, fontWeight: 700,
            letterSpacing: 1.4, color: 'ACCENT' }}>401</Text>
        <Text style={{ fontFamily: 'Noto Sans SC', fontSize: 17, color: '#FFFFFF',
            paddingLeft: 12 }}>说明文字</Text>
    </Box>
</Box>
```

**绝对定位锚定（页脚上方）**
```jsx
<Box style={{ position: 'absolute', left: 60, bottom: 60, width: 1160 }}>
    <Text style={{ fontFamily: 'Noto Sans SC', fontSize: 32, fontWeight: 700,
        color: '#FFFFFF' }}>金句第一行</Text>
</Box>
```

---

## 九、编译产物说明

slidep 生成的 PPTX 有两个和标准 PPTX 不同的点，改前要知道：

1. **媒体目录是 `ppt/slides/media/`**（不是标准的 `ppt/media/`），引用关系自洽
2. **页面尺寸是 1280×720 逻辑像素**，导出到 PowerPoint 后按实际物理尺寸显示

用 `python-pptx` 打开、校验媒体引用是否断链：

```python
import zipfile, re, posixpath
z = zipfile.ZipFile('deck.pptx')
for n in z.namelist():
    if re.match(r'ppt/slides/_rels/slide\d+\.xml\.rels$', n):
        for t in re.findall(r'Target="([^"]+)"', z.read(n).decode('utf8')):
            if 'media/' in t:
                p = posixpath.normpath(posixpath.join('ppt/slides', t))
                assert p in z.namelist(), (n, t)
```
