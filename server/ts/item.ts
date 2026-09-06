import {Entity} from './entity';

export class Item extends Entity {

  /**
   *
   * @type {boolean}
   */
  isStatic = false;

  /**
   *
   * @type {boolean}
   */
  isFromChest = false;

  /**
   *
   */
  blinkTimeout;

  /**
   *
   */
  despawnTimeout;

  /**
   *
   */
  respawn_callback;

  /**
   *
   * @param id
   * @param kind
   * @param x
   * @param y
   */
  constructor(id, kind, x, y) {
    super(id, 'item', kind, x, y);
  }

  /**
   *
   * @param params
   */
  handleDespawn(params) {
    const self = this;

    this.blinkTimeout = setTimeout(function () {
      params.blinkCallback();
      self.despawnTimeout = setTimeout(params.despawnCallback, params.blinkingDuration);
    }, params.beforeBlinkDelay);
  }

  /**
   *
   */
  destroy() {
    if (this.blinkTimeout) {
      clearTimeout(this.blinkTimeout);
    }
    if (this.despawnTimeout) {
      clearTimeout(this.despawnTimeout);
    }
    if (this.isStatic) {
      this.scheduleRespawn(30000);
    }
  }

  /**
   *
   * @param delay
   */
  scheduleRespawn(delay) {
    const self = this;
    setTimeout(function () {
      if (self.respawn_callback) {
        self.respawn_callback();
      }
    }, delay);
  }

  /**
   *
   * @param callback
   */
  onRespawn(callback) {
    this.respawn_callback = callback;
  }
}
