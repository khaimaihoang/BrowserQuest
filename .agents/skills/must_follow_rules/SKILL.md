---
name: twokone-word-chain-workflow
description: Guidelines and architectural rules for TwoKone Word Chain.
---

# TwoKone Word Chain Workflow

1. **Stack**: Python FastAPI backend (`Assets/Python/server.py`) + Kaplay.js frontend (`Assets/JavaScript/game-world.js`). Not a Unity project.
2. **Codebase Memory (MCP)**: Prioritize `codebase-memory-mcp` (`search_graph`, `trace_path`, `get_code_snippet`, `get_architecture`) over file/grep searches for code discovery to save tokens.
3. **Agent Behavior**: Concise answers (≤3 sentences unless code needed). Prefer in-place edits over rewrites. Read only necessary files. Avoid adding comments, docstrings, or type hints unless already present.
4. **Data-Driven**: All stats, IDs, and parameters belong in `Assets/Configs/*.yaml` or SQLite. Update `.schema.yaml` and enum loaders (`game_state.py`) when adding new types. No inline fallback data objects in JS.
5. **Localization**: All UI text lives in `strings.js` / `strings.py`. When adding configs on disk manually, add localized entries to `Assets/JavaScript/config-strings.js`.
6. **Modularity**: Never merge modular `game-world-*.js` files into a monolith. Read and edit only the narrowest scope file.
7. **Event-Driven (EDA)**: Decouple frontend modules via Kaplay events (`k.trigger` / `k.on`). No state polling in update loops. Backend WebSocket streams are the absolute source of truth.
8. **Documentation**: Update `architecture.md` or `.github/instructions/` only when introducing major architectural/protocol changes or when explicitly requested.
9. **Quality Assurance**: Verify syntax, typos, and config enum mappings before concluding tasks.
10. **Pixel UI & Typography Ruling**: All UI layouts in `ui_layouts.yaml` MUST use 1:1 unscaled sprite pixels (`width: 160px`, `height: 24px`, `padding: 8px`). Font sizes MUST follow the 8px bitmap grid (`fontSize: 8px` base, `16px` large). NEVER use non-8px multiples (no 6px, 10px, 11px, 13px, 14px). Text colors: Primary (`#f8fbff`), Secondary (`#9bb0c1`), Tertiary (`#536779`), Accent (`#f6c445`), Danger (`#ff5c5c`). Button height standard is `24px` with `padding: 0 calc(6px * var(--pixel-scale)) calc(4px * var(--pixel-scale)) calc(6px * var(--pixel-scale))` to optically center Vietnamese ascenders and descenders. `ui-layout-builder.html` must remain in strict 1-to-1 visual parity with `localhost:8000`.
11. **Visual Self-Testing, UI Constraints & Token Optimization**: Chú ý các lỗi UI thường gặp: (1) Hover effect tuyệt đối không dùng scale lẻ (tránh vỡ pixel); (2) Động tác kéo thả (drag) phải cache tọa độ DOM lúc pointerdown, cấm đo đạc lại ở pointermove để tránh lag; (3) Dynamic Prefab (con) phải bật cờ `isWidget: true` trong YAML để không bị dính `position: absolute`; (4) Disable button phải dùng `.removeAttribute("disabled")` để kích hoạt CSS observer. Sau khi sửa đổi giao diện, phải test headless E2E (cdp). Verify visual accuracy (geometry, pixel alignment, subpixel rendering, state transitions). Optimize token usage by inspecting compact JSON assertion outputs or tight element crops rather than dumping large full-screen base64 logs, and always clean up temporary screenshot artifacts from the root directory.
12. **OOP & SOLID Principles**: Strictly adhere to Object-Oriented Programming (OOP) paradigms and SOLID principles across the entire codebase (both Python backend and JS frontend).
    - **Single Responsibility (SRP)**: Classes and modules must have only one reason to change. Separate core game logic, networking, and UI rendering cleanly.
    - **Open/Closed (OCP)**: Design systems (especially Buffs, Entities, and UI Components) to be open for extension but closed for modification. Utilize polymorphism instead of massive `if/else` or `switch` statements.
    - **Liskov Substitution (LSP)** & **Interface Segregation (ISP)**: Subclasses must be substitutable for base classes. Keep interfaces/methods focused and narrow.
    - **Dependency Inversion (DIP)**: Depend on abstractions rather than concrete implementations. Use dependency injection (e.g., passing networking or config instances) rather than hardcoding global singletons where possible.
    - Strictly enforce **Encapsulation**: Avoid directly mutating global state, and ensure data fields are updated only through well-defined methods.
