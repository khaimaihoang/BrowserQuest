import {Character} from '../character';

export class Mob extends Character {

  aggroRange = 1;
  isAggressive = true;

  constructor(id, kind) {
    super(id, kind);
  }
}
