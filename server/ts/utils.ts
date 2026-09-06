import * as sanitizer from 'sanitizer';
import {Types} from '../../shared/ts/gametypes';

export class Utils {

  static sanitize(string) {
    // Strip unsafe tags, then escape as html entities.
    return sanitizer.escape(sanitizer.sanitize(string));
  }

  static random(range) {
    return Math.floor(Math.random() * range);
  }

  static randomRange(min, max) {
    return min + (Math.random() * (max - min));
  }

  static randomInt(min, max) {
    return min + Math.floor(Math.random() * (max - min + 1));
  }

  static clamp(min, max, value) {
    if (value < min) {
      return min;
    } else if (value > max) {
      return max;
    } else {
      return value;
    }
  }

  static randomOrientation() {
    var o, r = Utils.random(4);

    if (r === 0)
      o = Types.Orientations.LEFT;
    if (r === 1)
      o = Types.Orientations.RIGHT;
    if (r === 2)
      o = Types.Orientations.UP;
    if (r === 3)
      o = Types.Orientations.DOWN;

    return o;
  }

  static Mixin(target, source) {
    if (source) {
      for (var key, keys = Object.keys(source), l = keys.length; l--;) {
        key = keys[l];

        if (source.hasOwnProperty(key)) {
          target[key] = source[key];
        }
      }
    }
    return target;
  }

  static distanceTo(x, y, x2, y2) {
    var distX = Math.abs(x - x2);
    var distY = Math.abs(y - y2);

    return (distX > distY) ? distX : distY;
  }
}
