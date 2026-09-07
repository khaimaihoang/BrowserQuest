import {sprites} from '../sprites';
import {Animation} from '../animation';

export class Sprite {

  id;
  name;
  scale;
  filepath;
  animationData;
  width;
  height;
  isLoaded = false;
  offsetX = 0;
  offsetY = 0;
  image: any;

  isMulti = false;
  basePath = '';
  multiImages: { [key: string]: any } = {};
  imagesLoaded = 0;
  totalImages = 0;

  onload_func;
  whiteSprite;
  silhouetteSprite;

  constructor(name, scale) {
    this.name = name;
    this.scale = scale;

    this.loadJSON(sprites[name]);
  }

  loadJSON(data) {
    this.id = data.id;
    this.animationData = data.animations;
    this.width = data.width;
    this.height = data.height;
    this.offsetX = (data.offset_x !== undefined) ? data.offset_x : -16;
    this.offsetY = (data.offset_y !== undefined) ? data.offset_y : -16;

    if (data.is_multi) {
      this.isMulti = true;
      this.basePath = data.base_path || '';
      this.loadMulti();
    } else {
      this.filepath = 'img/' + this.scale + '/' + this.id + '.png';
      this.load();
    }
  }

  loadMulti() {
    var self = this;
    var uniqueFiles = new Set<string>();

    for (var name in this.animationData) {
      if (this.animationData[name].file) {
        uniqueFiles.add(this.animationData[name].file);
      }
    }

    this.totalImages = uniqueFiles.size;
    if (this.totalImages === 0) {
      this.isLoaded = true;
      if (this.onload_func) {
        this.onload_func();
      }
      return;
    }

    uniqueFiles.forEach(file => {
      var img = new Image();
      img.crossOrigin = 'Anonymous';
      // Load directly from basePath without scaling directory logic
      img.src = this.basePath + file + '?cb=' + new Date().getTime();
      
      img.onload = () => {
        self.multiImages[file] = img;
        self.imagesLoaded++;
        if (self.imagesLoaded === self.totalImages) {
          self.isLoaded = true;
          if (self.onload_func) {
            self.onload_func();
          }
        }
      };
      
      img.onerror = () => {
        console.error('Failed to load sprite image: ' + this.basePath + file);
        self.imagesLoaded++;
        if (self.imagesLoaded === self.totalImages) {
          self.isLoaded = true;
          if (self.onload_func) {
            self.onload_func();
          }
        }
      };
    });
  }

  getImage(animName?: string) {
    if (this.isMulti && animName && this.animationData[animName]) {
      let file = this.animationData[animName].file;
      return file ? this.multiImages[file] : null;
    }
    return this.image;
  }

  getOffset(animName?: string) {
    if (this.isMulti && animName && this.animationData[animName]) {
      let animData = this.animationData[animName];
      let ox = animData.offset_x !== undefined ? animData.offset_x : this.offsetX;
      let oy = animData.offset_y !== undefined ? animData.offset_y : this.offsetY;
      return { x: ox, y: oy };
    }
    return { x: this.offsetX, y: this.offsetY };
  }

  load() {
    var self = this;

    this.image = new Image();
    this.image.crossOrigin = 'Anonymous';
    this.image.src = this.filepath + '?cb=' + new Date().getTime();

    this.image.onload = function () {
      self.isLoaded = true;

      if (self.onload_func) {
        self.onload_func();
      }
    };
  }

  createAnimations() {
    var animations = {};

    for (var name in this.animationData) {
      var a = this.animationData[name];
      animations[name] = new Animation(name, a.length, a.row, this.width, this.height);
    }

    return animations;
  }

  createHurtSprite() {
    if (this.isMulti || !this.image) return;

    var canvas = document.createElement('canvas'),
      ctx = canvas.getContext('2d'),
      width = this.image.width,
      height = this.image.height,
      spriteData, data;

    canvas.width = width;
    canvas.height = height;
    ctx.drawImage(this.image, 0, 0, width, height);

    try {
      spriteData = ctx.getImageData(0, 0, width, height);

      data = spriteData.data;

      for (var i = 0; i < data.length; i += 4) {
        data[i] = 255;
        data[i + 1] = data[i + 2] = 75;
      }

      ctx.putImageData(spriteData, 0, 0);

      this.whiteSprite = {
        image: canvas,
        isLoaded: true,
        offsetX: this.offsetX,
        offsetY: this.offsetY,
        width: this.width,
        height: this.height,
        getImage: function() { return this.image; },
        getOffset: function() { return { x: this.offsetX, y: this.offsetY }; }
      };
    } catch (e) {
      console.error('Error getting image data for sprite : ' + this.name, e);
    }
  }

  getHurtSprite() {
    return this.whiteSprite;
  }

  createSilhouette() {
    if (this.isMulti || !this.image) return;

    var canvas = document.createElement('canvas'),
      ctx = canvas.getContext('2d'),
      width = this.image.width,
      height = this.image.height,
      spriteData, finalData, data;

    canvas.width = width;
    canvas.height = height;
    ctx.drawImage(this.image, 0, 0, width, height);
    data = ctx.getImageData(0, 0, width, height).data;
    finalData = ctx.getImageData(0, 0, width, height);
    let fdata = finalData.data;

    var getIndex = function (x, y) {
      return ((width * (y - 1)) + x - 1) * 4;
    };

    var getPosition = function (i) {
      var x, y;

      i = (i / 4) + 1;
      x = i % width;
      y = ((i - x) / width) + 1;

      return {x: x, y: y};
    };

    var hasAdjacentPixel = function (i) {
      var pos = getPosition(i);

      if (pos.x < width && !isBlankPixel(getIndex(pos.x + 1, pos.y))) {
        return true;
      }
      if (pos.x > 1 && !isBlankPixel(getIndex(pos.x - 1, pos.y))) {
        return true;
      }
      if (pos.y < height && !isBlankPixel(getIndex(pos.x, pos.y + 1))) {
        return true;
      }
      if (pos.y > 1 && !isBlankPixel(getIndex(pos.x, pos.y - 1))) {
        return true;
      }
      return false;
    };

    var isBlankPixel = function (i) {
      if (i < 0 || i >= data.length) {
        return true;
      }
      return data[i] === 0 && data[i + 1] === 0 && data[i + 2] === 0 && data[i + 3] === 0;
    };

    for (var i = 0; i < data.length; i += 4) {
      if (isBlankPixel(i) && hasAdjacentPixel(i)) {
        fdata[i] = fdata[i + 1] = 255;
        fdata[i + 2] = 150;
        fdata[i + 3] = 150;
      }
    }

    ctx.putImageData(finalData, 0, 0);

    this.silhouetteSprite = {
      image: canvas,
      isLoaded: true,
      offsetX: this.offsetX,
      offsetY: this.offsetY,
      width: this.width,
      height: this.height
    };
  }
}
