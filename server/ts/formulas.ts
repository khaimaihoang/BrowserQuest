import {Utils} from './utils';

export class Formulas {

  /**
   *
   * @param weaponLevel
   * @param armorLevel
   * @returns {any}
   */
  static dmg(weaponLevel, armorLevel) {
    var dealt = weaponLevel * Utils.randomInt(5, 10),
      absorbed = armorLevel * Utils.randomInt(1, 3),
      dmg = dealt - absorbed;

    if (dmg <= 0) {
      return Utils.randomInt(0, 3);
    } else {
      return dmg;
    }
  }

  /**
   *
   * @param armorLevel
   * @returns {number}
   */
  static hp(armorLevel) {
    return 80 + ((armorLevel - 1) * 30);
  }
}
