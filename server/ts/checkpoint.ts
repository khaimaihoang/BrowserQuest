import {Utils} from './utils';

export class Checkpoint {
  id;
  x;
  y;
  width;
  height;

  constructor(id, x, y, width, height) {
    this.id = id;
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
  }

  getRandomPosition() {
    return {
      x: this.x + Utils.randomInt(0, this.width - 1),
      y: this.y + Utils.randomInt(0, this.height - 1)
    };
  }
}
