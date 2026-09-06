import {Game} from '../game';
import {DamageInfo} from './damage.info';

import * as _ from 'lodash';

export class InfoManager {

  game: Game;
  infos = {};
  destroyQueue = [];

  constructor(game: Game) {
    this.game = game;
  }


  addDamageInfo(value, x, y, type) {
    var time = this.game.currentTime,
      id = time + '' + Math.abs(value) + '' + x + '' + y,
      self = this,
      info = new DamageInfo(id, value, x, y, DamageInfo.DURATION, type);

    info.onDestroy(function (id) {
      self.destroyQueue.push(id);
    });
    this.infos[id] = info;
  }

  forEachInfo(callback) {
    var self = this;

    _.each(this.infos, function (info, id) {
      callback(info);
    });
  }

  update(time) {
    var self = this;

    this.forEachInfo(function (info) {
      info.update(time);
    });

    _.each(this.destroyQueue, function (id) {
      delete self.infos[id];
    });
    this.destroyQueue = [];
  }
}
