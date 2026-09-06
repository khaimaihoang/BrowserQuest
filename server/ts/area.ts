import * as _ from 'lodash';
import {Utils} from './utils';

export class Area {

  id;
  x;
  y;
  width;
  height;
  world;
  entities = [];
  hasCompletelyRespawned = true;
  nbEntities;
  empty_callback;

  /**
   *
   * @param id
   * @param x
   * @param y
   * @param width
   * @param height
   * @param world
   */
  constructor(id, x, y, width, height, world) {
    this.id = id;
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.world = world;

  }

  _getRandomPositionInsideArea() {
    var pos: any = {},
      valid = false;

    while (!valid) {
      pos.x = this.x + Utils.random(this.width + 1);
      pos.y = this.y + Utils.random(this.height + 1);
      valid = this.world.isValidPosition(pos.x, pos.y);
    }
    return pos;
  }

  removeFromArea(entity) {
    var i = _.indexOf(_.pluck(this.entities, 'id'), entity.id);
    this.entities.splice(i, 1);

    if (this.isEmpty() && this.hasCompletelyRespawned && this.empty_callback) {
      this.hasCompletelyRespawned = false;
      this.empty_callback();
    }
  }

  addToArea(entity) {
    if (entity) {
      this.entities.push(entity);
      entity.area = this;
    }

    if (this.isFull()) {
      this.hasCompletelyRespawned = true;
    }
  }

  setNumberOfEntities(nb) {
    this.nbEntities = nb;
  }

  isEmpty() {
    return !_.any(this.entities, function (entity) {
      return !entity.isDead
    });
  }

  isFull() {
    return !this.isEmpty() && (this.nbEntities === _.size(this.entities));
  }

  onEmpty(callback) {
    this.empty_callback = callback;
  }
}
