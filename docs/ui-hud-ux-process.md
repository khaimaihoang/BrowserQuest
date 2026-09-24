# Quy Trình & Chuẩn Phát Triển UI / HUD / UX

> **Trạng thái:** Chuẩn bắt buộc (MUST-FOLLOW) cho mọi agent và lập trình viên
> khi thêm/sửa UI, HUD, UX trong dự án BrowserQuest.
>
> **Phương án đã chốt: Option A — Tách nhẹ, không đổi build.**
> Giữ nguyên webpack + jQuery + cơ chế copy CSS tĩnh; tách file theo feature bằng
> CSS `@import` + module TS trong `client/ts/ui/`; dùng dev server HMR đã có sẵn.
>
> **Tài liệu liên quan:**
> - [ui-hud-architecture-guide.md](./ui-hud-architecture-guide.md) — kiến trúc UI hiện tại
> - [kaetram-ui-review.md](./kaetram-ui-review.md) — mẫu tham chiếu Kaetram
> - `.agents/rules/ui-code.md` — ràng buộc UI
> - `AGENTS.md` §2, §5, §8, §10, §11

---

## 0. Mục đích

Chuẩn hoá cách làm UI/HUD/UX để:

1. **Tách file theo feature** — không còn 1 file `main.css` 89KB hay 1 `app.ts` ôm hết DOM.
2. **Dev server + HMR** — sửa UI thấy ngay, không phải rebuild tay.
3. **Contract rõ ràng** — agent sau biết chính xác tạo file nào, đặt tên gì, nối dây ra sao.
4. **Không phá kiến trúc** — `game.ts` vẫn DOM-free; UI không sở hữu game state.

### Vì sao chọn Option A (không phải Option B/SCSS)

| Tiêu chí | Option A (chốt) | Option B (đã thử, revert) |
|---|---|---|
| Đổi build/webpack | Không | Phải thêm `sass-loader`/`css-loader`/… |
| Rủi ro | Thấp | Cao (ảnh hưởng prod build, asset) |
| Dev server | Dùng cái đang có | Cấu hình lại |
| Tách feature | CSS `@import` + TS module | SCSS 7-1 partials |
| Phù hợp hiện tại | ✅ | Khi cần preprocessor thật |

> Option B từng được dựng thử rồi **revert** vì phát sinh lỗi prod build (EMFILE khi
> copy Minifantasy) và không cần thiết cho mục tiêu tách file. Quay lại Option A.

---

## 1. Kiến trúc mục tiêu (Option A)

```
client/
├── index.html                     # markup HUD (giữ nguyên)
├── css/
│   ├── main.css                   # ENTRY: chỉ chứa các dòng @import feature
│   ├── achievements.css           # (giữ)
│   ├── ie.css                     # (giữ)
│   ├── healthbar.css              # 1 file / feature (migrate dần khỏi main.css)
│   ├── bubbles.css
│   ├── chatbox.css
│   ├── population.css
│   └── notifications.css
└── ts/
    ├── game.ts                    # logic game — CẤM đụng DOM
    ├── main.ts                    # bootstrap / wiring
    ├── app.ts                     # controller intro/login (giữ)
    └── ui/                        # ★ TẦNG UI MỚI
        ├── healthbar.ui.ts        # 1 module / feature
        ├── bubbles.ui.ts
        ├── notifications.ui.ts
        ├── population.ui.ts
        └── <feature-moi>.ui.ts
```

**Nguyên tắc tầng:**

```
server (socket.io)
   └─► game.ts            (state, KHÔNG DOM)  ── phát callback onXxx()
         └─► main.ts        (wiring)             ── game.onXxx → ui module
               └─► ui/*.ui.ts (1 feature: DOM + CSS class toggle)
```

---

## 2. Dev server & HMR (KHÔNG đổi build)

Dự án **đã có sẵn** dev server, không cần cấu hình thêm:

```jsonc
// package.json
"watch:client": "webpack serve --env NODE_ENV=dev --config ./webpack.config.js --mode development"
```

| Đặc tính | Giá trị |
|---|---|
| Lệnh | `npm run watch:client` |
| Port | `8008` |
| HMR | `hot: true` |
| Static watch | thư mục `client/` (bỏ qua `Minifantasy`) |
| CSS | file trong `client/css/` được devServer theo dõi → sửa là tự reload |
| TS | webpack xử lý `client/ts/**` → HMR |

**Hệ quả cho quy trình:** sửa `.css`, `.html`, `.ts` đều thấy kết quả ngay trên trình
duyệt — **không cần thêm dependency hay sửa `webpack.config.js`.**

> Quy trình: `npm run watch:client` → mở `http://localhost:8008` → sửa UI → xem live.
> Kết hợp browser DevTools (Inspect Element) để thử style.

---

## 3. Cấu trúc & quy ước

### 3.1 CSS — tách theo feature

- `client/css/main.css` là **entry**, chỉ nên chứa các dòng `@import` ở **đầu file**
  (CSS yêu cầu `@import` phải đứng trước mọi rule khác):
  ```css
  @import 'healthbar.css';
  @import 'bubbles.css';
  @import 'notifications.css';
  ```
- Mỗi feature một file **phẳng trong `client/css/`** (không lồng thư mục con) để giữ
  nguyên độ sâu đường dẫn asset hiện tại (`url('../img/...')`).
- **Migrate dần**: khi tách 1 feature khỏi `main.css`, cắt khối CSS tương ứng sang
  file mới rồi thêm `@import`; **không xoá trước khi chuyển xong**.

### 3.2 TS — module UI theo feature

- Mọi HUD/UI mới nằm trong `client/ts/ui/`, đặt tên `<feature>.ui.ts`, export một
  class (khuyến nghị) hoặc một hàm `init`.
- **Base class là tùy chọn** (khác Option B): chỉ tạo base chung khi có ≥3 HUD dùng
  chung hành vi show/hide.

---

## 4. Contract (nhẹ)

### 4.1 Trách nhiệm từng tầng

| Tầng | Được phép | CẤM |
|---|---|---|
| `game.ts` | Giữ state, phát callback `onXxx()` | Đụng DOM, jQuery, `document.*` |
| `main.ts` | Nối `game.onXxx → ui module` | Chứa logic hiển thị |
| `ui/*.ui.ts` | Cập nhật DOM/CSS class theo data | Sửa `game.player.*`, gọi mạng |

### 4.2 Mẫu module UI (không bắt buộc base class)

```ts
// client/ts/ui/healthbar.ui.ts
export class HealthBarUi {
  private bar = document.querySelector('#healthbar') as HTMLElement;
  private fill = document.querySelector('#hitpoints') as HTMLElement;

  public update(hp: number, maxHp: number): void {
    const pct = maxHp > 0 ? hp / maxHp : 0;
    this.fill.style.width = `${Math.round(this.bar.offsetWidth * pct)}px`;
  }

  public resize(): void { /* vẽ lại với state hiện tại */ }
}
```

### 4.3 jQuery

- Được phép dùng (đồng bộ với code hiện có), nhưng **mỗi module chỉ nên chọn 1 phong
  cách** (vanilla DOM *hoặc* jQuery) để dễ đọc.
- **MUST NOT** viết jQuery/DOM mới trong `game.ts`.

---

## 5. Naming Conventions

| Loại | Quy ước | Ví dụ |
|---|---|---|
| Module UI (TS) | `<feature>.ui.ts`, class `PascalCase` + `Ui` | `inventory.ui.ts` → `InventoryUi` |
| CSS feature | `<feature>.css` (phẳng trong `client/css/`) | `healthbar.css` |
| CSS entry | `main.css` (chỉ `@import`) | — |
| DOM id | `kebab-case` | `#bar-container`, `#healthbar` |
| DOM class trạng thái | `.active`, `.open`, `.hidden`, `.invincible` | — |
| Callback `game.ts` | `onXxx` | `onPlayerHealthChange` |

---

## 6. Recipe — Tạo một HUD mới (6 bước)

Ví dụ: thêm **thanh EXP/Level**.

**Bước 1 — Markup.** Thêm `<div>` trong `client/index.html` (đúng vùng, ví dụ trong
`#bar-container`):
```html
<div id="expbar"><div id="expfill"></div></div>
```

**Bước 2 — CSS feature.** Tạo `client/css/expbar.css`, rồi thêm `@import 'expbar.css';`
vào **đầu** `client/css/main.css`. Giữ độ sâu `url('../img/...')` đúng.

**Bước 3 — Module UI.** Tạo `client/ts/ui/expbar.ui.ts`:
```ts
import { ExpBarUi } from './expbar.ui'; // trong main.ts, không phải ở đây
export class ExpBarUi {
  private bar = document.querySelector('#expbar') as HTMLElement;
  private fill = document.querySelector('#expfill') as HTMLElement;
  public update(cur: number, max: number): void {
    const pct = max > 0 ? cur / max : 0;
    this.fill.style.width = `${Math.round(this.bar.offsetWidth * pct)}px`;
  }
  public resize(): void { /* vẽ lại */ }
}
```

**Bước 4 — Nối callback.** Trong `client/ts/main.ts`, khởi tạo và nối:
```ts
import { ExpBarUi } from './ui/expbar.ui';
const expBar = new ExpBarUi();
game.onPlayerHealthChange((hp, maxHp) => expBar.update(hp, maxHp)); // thay bằng event EXP
```
`game.ts` MUST chỉ phát callback (không DOM).

**Bước 5 — Resize.** Gọi `expBar.resize()` trong `app.resizeUi()`.

**Bước 6 — Test & self-review.** Chạy checklist §7 (tối thiểu 10 vòng, xem §9).

---

## 7. Checklist Production-Ready (MUST pass trước khi bàn giao)

- [ ] `game.ts` **không** có DOM/jQuery (`document`, `$(`) — đã kiểm tra.
- [ ] HUD mới nằm trong `client/ts/ui/`, không nhét vào `app.ts`.
- [ ] CSS tách thành file feature, đã thêm `@import` ở đầu `main.css`.
- [ ] Đường dẫn asset (`url('../img/...')`) đúng độ sâu.
- [ ] **Không** hardcode string hiển thị — dùng/i18n hoá (xem ràng buộc `ui-code.md`).
- [ ] Trạng thái dùng class-toggle + CSS transition (đồng bộ toàn UI).
- [ ] Hoạt động ở cả 3 tỉ lệ (1x/2x/3x); test tối thiểu 480px → max resolution.
- [ ] Không chặn game loop; mọi `setTimeout`/`setInterval` đều được clear.
- [ ] Animation tôn trọng `prefers-reduced-motion`.
- [ ] Có `resize()` và được gọi trong `app.resizeUi()`.
- [ ] Đã tự test ≥10 vòng: vào game, tương tác, resize, mobile/tablet.

---

## 8. Anti-Patterns (CẤM)

| # | Cấm | Vì sao |
|---|---|---|
| 1 | Thêm logic DOM mới vào `game.ts` | Phá tách biệt state/UI |
| 2 | Nhồi thêm HUD mới trực tiếp vào `app.ts` | `app.ts` chỉ còn intro/login |
| 3 | Thêm CSS nguyên khối vào `main.css` (ngoài `@import`) | Phải tách file feature |
| 4 | Đặt file CSS feature vào thư mục con lồng sâu | Lệch `url('../img/...')` |
| 5 | Query DOM trong `update()` mỗi frame | Phải cache trong constructor |
| 6 | UI sửa trực tiếp `game.player.*` | UI chỉ đọc/phát event |
| 7 | Hardcode string/`innerHTML` tiếng Anh | Vi phạm `ui-code.md` |
| 8 | `setInterval` không clear | Rò rỉ, chặn tài nguyên |
| 9 | Sửa `webpack.config.js`/thêm dependency cho UI | Option A không đổi build |
| 10 | Đọc file ngoài phạm vi khi sửa HUD | Tuân thủ `codebase-reading.md` |

---

## 9. Quy trình làm việc của Agent khi làm UI/HUD

1. **Đọc rules trước**: `AGENTS.md`, `.agents/rules/ui-code.md`,
   `.agents/rules/codebase-reading.md`, tài liệu này.
2. **Khảo sát tối thiểu**: dùng `codebase-memory-mcp`; chỉ đọc đúng file/khối cần
   (span ≤ 800 dòng, ≤ 2–3 lần/file/lượt).
3. **Đề xuất phương án**: 2–4 lựa chọn nếu có quyết định kiến trúc (AGENTS.md §5).
4. **Sửa đơn file mặc định**: mỗi lượt 1 file đích, trừ khi feature buộc nhiều file.
5. **Tự kiểm thử ≥10 vòng** (AGENTS.md §10): `npm run watch:client`, tương tác, resize,
   kiểm tra không còn TODO/debug/placeholder.
6. **Báo cáo**: file đã sửa (link `file:///...`), diff ±5 dòng ngữ cảnh, 1 câu tóm tắt.
7. **Header bắt buộc** ở đầu mọi câu trả lời (AGENTS.md §8):
   `Token used: ... | Rules read: ... | Tools used: ...`

---

## 10. Việc cần làm một lần (chưa áp dụng)

- Cập nhật `paths` trong `.agents/rules/ui-code.md` để rule UI tự nạp khi sửa
  `client/ts/ui/**`, `client/css/**`, `client/index.html`:
  ```yaml
  paths:
    - "client/ts/ui/**"
    - "client/css/**"
    - "client/index.html"
  ```
  (Hiện tại đang là `src/ui/**` — không khớp thư mục thật.)

---

## 11. Tham chiếu chéo

- Kaetram dùng mô hình class-per-interface + SCSS 7-1 — xem
  [kaetram-ui-review.md](./kaetram-ui-review.md) §4. Đây là hướng nâng cấp tương lai,
  không thuộc Option A.
- Kiến trúc UI hiện tại của BrowserQuest — xem
  [ui-hud-architecture-guide.md](./ui-hud-architecture-guide.md).
