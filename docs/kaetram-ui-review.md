# Kaetram-Open UI Architecture Review

> Tài liệu tham chiếu nội bộ — phân tích cách fork **Kaetram-Open** (v0.5.5, OmniaDev)
> của BrowserQuest tổ chức UI/HUD, để làm mẫu khi refactor HUD cho BrowserQuest.
>
> Repo được review: `D:\Develop\Projects\Kaetram-Open`
> Mối liên hệ: Kaetram giữ asset của BrowserQuest nhưng **code viết lại từ đầu**,
> đúng hướng "Option B (refactor)" đã đề xuất trong
> [ui-hud-architecture-guide.md](./ui-hud-architecture-guide.md).

---

## 1. Tổng quan stack

| Thành phần | Công nghệ |
|---|---|
| Framework | **Astro** (SSR/SSG) + TypeScript |
| Styling | **SCSS (7-1 architecture)** |
| Monorepo | Yarn workspaces (`packages/*`) |
| DOM | vanilla `document.querySelector` + `classList` — **bỏ jQuery** |
| i18n | `@kaetram/common/i18n` (`t()`, `dir()`, `getLanguage()`) |

---

## 2. Cấu trúc thư mục UI

| Thư mục | Vai trò |
|---|---|
| `packages/client/components/game.astro` (38KB) | Toàn bộ markup UI in-game — 8 canvas + mọi interface container (`#health`, `#mana`, `#profile-container`, `#inventory`, `#bank`…) |
| `packages/client/components/intro.astro` | UI login / tạo nhân vật |
| `packages/client/scss/` | SCSS 7-1: `abstracts/` (media, sprite), `base/`, `app/` (intro), `game/` — mỗi feature 1 partial (`_inventory.scss`, `_bank.scss`, `_equipments.scss`…) |
| `packages/client/src/controllers/` | `hud.ts`, `menu.ts`, `input.ts`, `chat.ts`, `audio.ts`, `entities.ts`, `pointer.ts`, `joystick.ts`… |
| `packages/client/src/menu/` | 1 class cho mỗi interface (inventory, bank, store, profile, equipments, crafting, trade, guilds…) |
| `packages/client/src/app.ts` | Controller login/intro (parchment, worlds, validation) |
| `packages/client/src/game.ts` | Logic game in-game |

---

## 3. UI là DOM overlay (không vẽ canvas)

Giống BrowserQuest — thế giới render lên canvas, UI là `<div>` đè lên. Nhưng Kaetram
dùng **8 canvas**:

`background`, `entities`, `entities-fore`, `foreground`, `entities-mask`, `cursor`,
`overlay`, `text-canvas`.

---

## 4. Hệ thống Menu hướng đối tượng (khác biệt lớn nhất)

### Abstract base — `src/menu/menu.ts`

```ts
constructor(containerName, closeButton, toggleButton)  // selector CSS
show() / hide() / toggle() / isVisible() / resize()
batch() / synchronize() / add() / remove()             // đồng bộ data từ server
onShow(callback)                                       // ẩn menu khác khi mở
```

### Registry — `src/controllers/menu.ts` (`MenuController`)

```ts
this.menus = { inventory, bank, store, profile, equipments, ... };  // 21 menu
menuController.get(identifier)      // tra cứu theo network interface ID
menuController.hide()               // ẩn tất cả
menuController.synchronize(key?)    // broadcast data sync
menuController.resize()             // broadcast resize
```

Mỗi menu là 1 subclass, nối nhau qua callback: `inventory.onSelect(...)`,
`bank.onSelect(...)`, `trade.onAccept(...)`…

---

## 5. Luồng dữ liệu = observer pattern ở tầng Entity

Thay vì `Game` phơi hàng chục callback, Kaetram đặt event emitter **trên Player**:

- `src/menu/header.ts` (thanh máu/mana) đăng ký `player.onHitPoints(cb)`,
  `player.onMana(cb)`, `player.onPoison(cb)`.
- `src/controllers/hud.ts` = thanh máu entity đang hover (`#attack-info`), có
  `updateCallback`.

Cập nhật DOM thuần vanilla:

```ts
maskElement.style.width = `${element.offsetWidth * (points / maxPoints)}px`;
textElement.textContent = `${points}/${maxPoints}`;
maskElement.classList.add('health-mask-white');   // flash khi bị đánh
```

---

## 6. So sánh BrowserQuest vs Kaetram

| Khía cạnh | BrowserQuest | Kaetram |
|---|---|---|
| DOM thao tác | jQuery | vanilla `querySelector` + `classList` |
| Tổ chức UI | 1 `app.ts` + 1 `main.css` 89KB | class/feature + SCSS partial |
| Hệ menu | ad-hoc toggle class | abstract `Menu` + `MenuController` registry |
| Event | `Game.onXxx(callback)` | emitter trên entity (Player/Mob) |
| i18n | không có (hardcode) | `@kaetram/common/i18n` `t()/dir()/getLanguage()` (RTL) |
| Responsive | media query 1x/2x/3x | `@custom-media --lg/--md/--sm` + scale 1.875/1.5/1 |
| Mobile | touch | joystick + zoom buttons + PWA |

---

## 7. Ghi chú

- **Vẫn còn gap**: menu client xây DOM bằng `document.createElement` với string tiếng
  Anh hardcode — i18n `t()` mới dùng ở server/Astro SSR, chưa phủ menu client.
- `abstracts/_media.scss` dùng **fractional scale** (1.875/1.5/1) thay vì integer —
  mượt hơn trên màn hình 2K/4K.

---

## 8. Kết luận

Kaetram giữ nguyên ý tưởng "DOM overlay trên canvas" của BrowserQuest nhưng nâng cấp
kiến trúc lên **Astro + SCSS 7-1 + class-per-interface + registry `MenuController` +
event emitter trên entity + i18n framework**. Đây là mẫu tham chiếu tốt cho việc
refactor HUD BrowserQuest (hướng Option B).
