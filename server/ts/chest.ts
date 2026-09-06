import {Item} from './item';
import {Types} from '../../shared/ts/gametypes';
import {Utils} from './utils';
import * as _ from 'lodash';

export class Chest extends Item {
  items;
  constructor(id, x, y) {
    super(id, Types.Entities.CHEST, x, y);
  }

  setItems(items) {
    this.items = items;
  }

  getRandomItem() {
    var nbItems = _.size(this.items),
      item = null;

    if (nbItems > 0) {
      item = this.items[Utils.random(nbItems)];
    }
    return item;
  }
}
