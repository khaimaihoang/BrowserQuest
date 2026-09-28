# client/ts/ui — Tầng UI / HUD

Thư mục chứa các module UI/HUD, **tách theo feature** (Option A).

## Quy ước (bắt buộc)

- Mỗi feature một file: `<feature>.ui.ts`, export class `PascalCase` + `Ui`.
  Ví dụ: `inventory.ui.ts` → `InventoryUi`.
- `game.ts` **MUST NOT** đụng DOM — chỉ phát callback `onXxx()`.
- `main.ts` nối `game.onXxx → ui module`.
- Module UI chỉ đọc/cập nhật DOM & CSS class; **không** sửa game state.
- CSS của feature nằm ở `client/css/<feature>.css`, thêm `@import` vào **đầu**
  `client/css/main.css` (file phẳng, giữ đúng độ sâu `url('../img/...')`).
- Có `resize()` và được gọi trong `app.resizeUi()`.
- Base class **tùy chọn**: chỉ tạo khi có ≥3 HUD dùng chung hành vi show/hide.

## Tham chiếu

- Quy trình đầy đủ: `docs/ui-hud-ux-process.md`
- Ràng buộc UI: `.agents/rules/ui-code.md`
- Kiến trúc UI hiện tại: `docs/ui-hud-architecture-guide.md`
- Mẫu nâng cấp tương lai (Kaetram): `docs/kaetram-ui-review.md`

## Trạng thái

Phase 0: scaffold thư mục + convention.
Phase 1: `panel.ui.ts` (`PanelUi`) — panel MiniFantasy 9-slice, display-only,
hiển thị bằng class `.active`, đóng bằng nút `.close` hoặc ESC; CSS tại
`client/css/panel.css`. `resize()` là no-op có chủ đích vì 9-slice tự co giãn
theo media query (giữ method để khớp contract). Thêm module mới theo recipe 6
bước trong `docs/ui-hud-ux-process.md`.
