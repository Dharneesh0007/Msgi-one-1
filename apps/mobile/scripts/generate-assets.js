/**
 * MSGI One - Asset Generation Script
 * Generates valid PNG images for icon.png, adaptive-icon.png, splash.png, splash-icon.png, favicon.png
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

// CRC32 table
const crcTable = new Uint32Array(256);
for (let i = 0; i < 256; i++) {
  let c = i;
  for (let j = 0; j < 8; j++) {
    c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
  }
  crcTable[i] = c;
}

function crc32(buf) {
  let crc = -1;
  for (let i = 0; i < buf.length; i++) {
    crc = (crc >>> 8) ^ crcTable[(crc ^ buf[i]) & 0xFF];
  }
  return (crc ^ -1) >>> 0;
}

function makeChunk(type, data) {
  const typeBuf = Buffer.from(type, 'ascii');
  const lenBuf = Buffer.alloc(4);
  lenBuf.writeUInt32BE(data.length, 0);
  const toCrc = Buffer.concat([typeBuf, data]);
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(toCrc), 0);
  return Buffer.concat([lenBuf, toCrc, crcBuf]);
}

function createPng(width, height, getPixel) {
  const sig = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);

  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; // 8 bits per channel
  ihdr[9] = 6; // RGBA
  ihdr[10] = 0; // deflate
  ihdr[11] = 0; // filter 0
  ihdr[12] = 0; // no interlace

  const rowLen = 1 + width * 4;
  const raw = Buffer.alloc(height * rowLen);
  let offset = 0;

  for (let y = 0; y < height; y++) {
    raw[offset++] = 0; // Filter: None
    for (let x = 0; x < width; x++) {
      const [r, g, b, a] = getPixel(x, y, width, height);
      raw[offset++] = r;
      raw[offset++] = g;
      raw[offset++] = b;
      raw[offset++] = a;
    }
  }

  const compressed = zlib.deflateSync(raw, { level: 9 });
  return Buffer.concat([
    sig,
    makeChunk('IHDR', ihdr),
    makeChunk('IDAT', compressed),
    makeChunk('IEND', Buffer.alloc(0))
  ]);
}

// Distance helper
function distToSegment(px, py, x1, y1, x2, y2) {
  const l2 = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1);
  if (l2 === 0) return Math.hypot(px - x1, py - y1);
  let t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (x1 + t * (x2 - x1)), py - (y1 + t * (y2 - y1)));
}

// Draw emblem logo onto pixel
function renderEmblem(px, py, width, height, transparentBg = false) {
  const cx = width / 2;
  const cy = height / 2;
  const scale = width / 1024;

  // Background
  let bgR = 26, bgG = 54, bgB = 93, bgA = transparentBg ? 0 : 255;
  if (!transparentBg) {
    // Subtle radial gradient
    const dFromCenter = Math.hypot(px - cx, py - cy) / (width * 0.7);
    const grad = Math.min(1, Math.max(0, dFromCenter));
    bgR = Math.round(26 * (1 - grad * 0.4));
    bgG = Math.round(54 * (1 - grad * 0.4));
    bgB = Math.round(93 * (1 - grad * 0.3));
  }

  // Geometry scaled to width/1024
  const strokeM = 40 * scale;
  const mTop = cy - 140 * scale;
  const mBot = cy + 150 * scale;
  const mMid = cy + 40 * scale;
  const leftX = cx - 150 * scale;
  const rightX = cx + 150 * scale;

  // Distances for M segments
  const d1 = distToSegment(px, py, leftX, mTop, leftX, mBot);
  const d2 = distToSegment(px, py, rightX, mTop, rightX, mBot);
  const d3 = distToSegment(px, py, leftX, mTop, cx, mMid);
  const d4 = distToSegment(px, py, rightX, mTop, cx, mMid);
  const minM = Math.min(d1, d2, d3, d4);

  // Outer ring (radius ~ 310)
  const ringRadius = 310 * scale;
  const ringDist = Math.abs(Math.hypot(px - cx, py - cy) - ringRadius);
  const ringWidth = 10 * scale;

  // Gold Star/Diamond at (cx, cy - 200)
  const starY = cy - 200 * scale;
  const starDist = Math.abs(px - cx) + Math.abs(py - starY);
  const starRadius = 28 * scale;

  // Network Nodes at 3 compass points
  const nodeDist1 = Math.hypot(px - (cx - ringRadius), py - cy);
  const nodeDist2 = Math.hypot(px - (cx + ringRadius), py - cy);
  const nodeDist3 = Math.hypot(px - cx, py - (cy + ringRadius));
  const nodeRadius = 16 * scale;
  const isNode = nodeDist1 <= nodeRadius || nodeDist2 <= nodeRadius || nodeDist3 <= nodeRadius;

  // Color blending
  // 1. Star (Gold #F59E0B -> 245, 158, 11)
  if (starDist <= starRadius) {
    const alpha = Math.min(1, Math.max(0, (starRadius - starDist) / scale + 0.5));
    return [
      Math.round(245 * alpha + bgR * (1 - alpha)),
      Math.round(158 * alpha + bgG * (1 - alpha)),
      Math.round(11 * alpha + bgB * (1 - alpha)),
      transparentBg ? Math.round(255 * alpha) : 255
    ];
  }

  // 2. Nodes (Cyan #38BDF8 -> 56, 189, 248)
  if (isNode) {
    return [56, 189, 248, 255];
  }

  // 3. Ring (Cyan/Teal #0EA5E9 -> 14, 165, 233)
  if (ringDist <= ringWidth) {
    const edgeAlpha = Math.min(1, Math.max(0, (ringWidth - ringDist) / scale + 0.5));
    return [
      Math.round(14 * edgeAlpha + bgR * (1 - edgeAlpha)),
      Math.round(165 * edgeAlpha + bgG * (1 - edgeAlpha)),
      Math.round(233 * edgeAlpha + bgB * (1 - edgeAlpha)),
      transparentBg ? Math.round(255 * edgeAlpha) : 255
    ];
  }

  // 4. M monogram (Pure White #FFFFFF -> 255, 255, 255)
  if (minM <= strokeM / 2) {
    const edgeAlpha = Math.min(1, Math.max(0, (strokeM / 2 - minM) / scale + 0.5));
    return [
      Math.round(255 * edgeAlpha + bgR * (1 - edgeAlpha)),
      Math.round(255 * edgeAlpha + bgG * (1 - edgeAlpha)),
      Math.round(255 * edgeAlpha + bgB * (1 - edgeAlpha)),
      transparentBg ? Math.round(255 * edgeAlpha) : 255
    ];
  }

  return [bgR, bgG, bgB, bgA];
}

const assetsDir = path.join(__dirname, '..', 'assets');
if (!fs.existsSync(assetsDir)) {
  fs.mkdirSync(assetsDir, { recursive: true });
}

console.log('Generating mobile assets in:', assetsDir);

// 1. icon.png (1024x1024, navy background)
console.log('Generating icon.png (1024x1024)...');
const iconPng = createPng(1024, 1024, (x, y, w, h) => renderEmblem(x, y, w, h, false));
fs.writeFileSync(path.join(assetsDir, 'icon.png'), iconPng);

// 2. adaptive-icon.png (1024x1024, transparent background for Android adaptive icon)
console.log('Generating adaptive-icon.png (1024x1024)...');
const adaptiveIconPng = createPng(1024, 1024, (x, y, w, h) => renderEmblem(x, y, w, h, true));
fs.writeFileSync(path.join(assetsDir, 'adaptive-icon.png'), adaptiveIconPng);

// 3. splash.png (1024x1024, navy background)
console.log('Generating splash.png (1024x1024)...');
const splashPng = createPng(1024, 1024, (x, y, w, h) => renderEmblem(x, y, w, h, false));
fs.writeFileSync(path.join(assetsDir, 'splash.png'), splashPng);

// 4. splash-icon.png (1024x1024, transparent background)
console.log('Generating splash-icon.png (1024x1024)...');
const splashIconPng = createPng(1024, 1024, (x, y, w, h) => renderEmblem(x, y, w, h, true));
fs.writeFileSync(path.join(assetsDir, 'splash-icon.png'), splashIconPng);

// 5. favicon.png (192x192, navy background)
console.log('Generating favicon.png (192x192)...');
const faviconPng = createPng(192, 192, (x, y, w, h) => renderEmblem(x, y, w, h, false));
fs.writeFileSync(path.join(assetsDir, 'favicon.png'), faviconPng);

console.log('All assets successfully generated:');
fs.readdirSync(assetsDir).forEach(file => {
  const stat = fs.statSync(path.join(assetsDir, file));
  console.log(` - ${file}: ${stat.size} bytes`);
});
