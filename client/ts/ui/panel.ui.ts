/**
 * UI Panel — MiniFantasy "Grim" 9-slice, theo format UI của BrowserQuest.
 *
 * Display-only: không sở hữu/sửa game state. Hiển thị dùng class state
 * `.active` (giống #instructions / #achievements), đóng qua nút `.close`
 * hoặc phím ESC.
 */
export class PanelUi {
  private panel: HTMLElement;
  private trigger: HTMLElement;
  private closeButton: HTMLElement;

  public constructor() {
    this.panel = document.querySelector('#ui-panel') as HTMLElement;
    this.trigger = document.querySelector('#ui-panel-trigger') as HTMLElement;
    this.closeButton = this.panel.querySelector('.close') as HTMLElement;

    this.trigger.addEventListener('click', () => this.toggle());
    this.closeButton.addEventListener('click', () => this.hide());

    document.addEventListener('keydown', (event: KeyboardEvent) => {
      if (event.key === 'Escape' && this.isVisible()) this.hide();
    });
  }

  /** Hiện panel. */
  public show(): void {
    this.panel.classList.add('active');
    this.trigger.classList.add('active');
  }

  /** Ẩn panel. */
  public hide(): void {
    this.panel.classList.remove('active');
    this.trigger.classList.remove('active');
  }

  /** Đảo trạng thái hiển thị. */
  public toggle(): void {
    if (this.isVisible()) this.hide();
    else this.show();
  }

  /** Panel có đang hiển thị không. */
  public isVisible(): boolean {
    return this.panel.classList.contains('active');
  }

  /** Hook resize — 9-slice tự co giãn, giữ method cho contract. */
  public resize(): void {}
}
