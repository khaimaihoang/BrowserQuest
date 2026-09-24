# UI/HUD Architecture Review & New HUD Creation Guide

> Tài liệu tham chiếu nội bộ — mô tả cách dự án BrowserQuest hiện tại xây dựng UI/HUD
> và quy trình chuẩn để thêm một HUD mới.
>
> Phạm vi áp dụng: `client/` (DOM + CSS + jQuery) và các rules `.agents/rules/ui-code.md`.

---

## 1. Nguyên tắc cốt lõi

**UI là HTML/CSS/jQuery, KHÔNG phải Canvas.**

Game render thế giới lên 3 lớp canvas (`background` → `entities` → `foreground`),
nhưng toàn bộ HUD là các thẻ `<div>` nằm đè lên canvas, được tô bằng CSS và thao tác
bằng jQuery (tải từ CDN).

---

## 2. Các tầng kiến trúc (Separation of Concerns)

| Tầng | File | Vai trò |
|------|------|---------|
| DOM / markup | `client/index.html` | Khai báo toàn bộ HUD: `#bar-container`, `#healthbar`, `#hitpoints`, `#weapon`, `#armor`, `#chatbox`, `#bubbles`, `#population`, `#achievement-notification`… |
| Style | `client/css/main.css` (89KB) + `client/css/achievements.css` | Sprite sheet nền, vị trí, animation, media queries theo 3 tỉ lệ (1x/2x/3x) |
| Game state | `client/ts/game.ts` — class `Game` | **KHÔNG đụng DOM.** Chỉ giữ state (`player.hitPoints`, `maxHitPoints`) và phát callback khi state đổi |
| UI controller | `client/ts/app.ts` — class `App` | **Tầng duy nhất** đụng `$()`/DOM. Nhận callback → cập nhật CSS |
| Wiring | `client/ts/main.ts` — hàm `initGame()` | Nối `game.onXxx(callback)` → `app.xxx()` → DOM |

---

## 3. Hợp đồng Game ↔ UI (Event/Callback)

`Game` chỉ phơi các hàm đăng ký callback (cuối `game.ts`, ~dòng 2216):

```ts
game.onGameStart(cb)
game.onPlayerHealthChange(cb)
game.onPlayerHurt(cb)
game.onPlayerDeath(cb)
game.onNbPlayersChange(cb)
game.onNotification(cb)
game.onPlayerEquipmentChange(cb)
game.onPlayerInvincible(cb)
game.onAchievementUnlock(cb)
game.onDisconnect(cb)
```

Luồng dữ liệu chuẩn (ví dụ thanh máu):

```
server (socket.io)
  → game.player.hitPoints thay đổi
  → game.updateBars()
  → playerhp_callback(hp, maxHp)   // đăng ký trong app.initHealthBar()
  → app chỉnh $('#hitpoints').css('width', ...)
  → CSS hiển thị
```

**Pattern lặp lại:** class-toggle (`.active`, `.started`, `.death`, `.invincible`,
`.white`, `.credits`…) + CSS transition cho mọi trạng thái/hoạt ảnh.

---

## 4. Ghi chú về độ lệch với rules

[.agents/rules/ui-code.md](../../.agents/rules/ui-code.md) yêu cầu localization,
gamepad và colorblind mode, nhưng code thực tế:

- **hardcode string** trong HTML;
- chỉ hỗ trợ chuột/phím/touch.

Khi tạo HUD mới: tối thiểu không làm gap này tệ hơn; ưu tiên bổ sung dần localization
và tôn trọng `prefers-reduced-motion`.

---

## 5. Hướng dẫn tạo HUD/UI mới — 3 lựa chọn

- **Option A (khuyến nghị — ít rủi ro):** Thêm HUD mới theo đúng pattern DOM+jQuery
  hiện có. Thêm `<div>` vào `index.html`, style vào `main.css`, wire callback trong
  `main.ts`. Nhất quán, dễ review, không đụng game state.
- **Option B (refactor trung hạn):** Gom mọi cập nhật HUD vào một module riêng trong
  `client/ts/interface/` (hiện chỉ có bubble/damage.info) để tách khỏi `app.ts` đang
  phình to. Tốt hơn về lâu dài, tốn công hơn.
- **Option C (đổi paradigm):** HUD vẽ trên canvas `foreground`. Chỉ dùng nếu HUD cần
  hiệu ứng pixel gắn với thế giới; phá vỡ kiến trúc hiện tại, không khuyến nghị.

---

## 6. Recipe chi tiết (Option A — ví dụ "thanh EXP/Level")

### Bước 1 — Khai báo DOM

Trong `client/index.html`, bên trong `#bar-container`:

```html
<div id="expbar"></div>
<div id="expfill"></div>
```

### Bước 2 — Style

Trong `client/css/main.css`, theo đúng 3 block tỉ lệ 1x/2x/3x đang có:

- dùng sprite `barsheet.png` (pattern có sẵn ở `#healthbar`/`#hitpoints`);
- đặt `position:absolute`;
- `background-size` theo scale.

### Bước 3 — Đăng ký callback

Trong `client/ts/main.ts → initGame()`:

```ts
game.onPlayerHealthChange(function (hp, maxHp) {  // thay bằng event EXP nếu có
  app.updateExpBar(hp, maxHp);
});
```

### Bước 4 — UI update

Trong `client/ts/app.ts` (chỉ DOM, không logic):

```ts
updateExpBar(cur, max) {
  const w = $('#expbar').width();
  $('#expfill').css('width', Math.round(w * cur / max) + 'px');
}
```

### Bước 5 — Gọi lại khi resize

Thêm vào `app.resizeUi()` cùng `initHealthBar()`/`updateBars()`.

---

## 7. Checklist Production-Ready (AGENTS.md §10)

1. UI **không** sửa game state — chỉ display + gọi event/command.
2. Mọi state đổi dùng class-toggle + CSS transition (đồng bộ với phần còn lại).
3. Thêm vào đủ 3 media-query tỉ lệ (1x/2x/3x); test min (480px) và max resolution.
4. Không hardcode string nếu feature có chữ hiển thị — cân nhắc thêm hệ localization.
5. Animation phải bỏ qua được (respect `prefers-reduced-motion`) — không lặp
   `setInterval` vô hạn.
6. Âm thanh (nếu có) đi qua audio event system, không gọi trực tiếp.
7. Không chặn game loop; mọi `setTimeout`/`setInterval` phải có
   `clearTimeout`/`clearInterval`.
8. Tự test ≥10 vòng: vào game, nhận sát thương, đổi equip, resize, mobile/tablet.
