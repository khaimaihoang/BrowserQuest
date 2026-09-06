import {Entity} from './entity';

export class Npc extends Entity {
  constructor(id, kind, x, y) {
    super(id, 'npc', kind, x, y);
  }

  destroy() {

  }
}
