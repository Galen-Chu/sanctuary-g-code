// Lineage verification: run the ORIGINAL abyssal-garden RNG / noise next to the
// Python port (scripts/verify_lineage.py). Both must print identical lines.
//
// Functions below are copied verbatim from Noniv/abyssal-garden source/src/math.js
// (MIT) on 2026-11-16 — only the driver code at the bottom is new. Do not "fix"
// anything here; the point is to execute the source implementation as-is.

let _seed = 20261110;
const rnd = () => {
  _seed = (_seed + 0x6D2B79F5) | 0;
  let t = Math.imul(_seed ^ (_seed >>> 15), 1 | _seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const mix = (a, b, t) => a + (b - a) * t;
const ihash = (x, y, z) => {
  let h = (Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(z, 1274126177)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
};
const vnoise = (x, y, z) => {
  const ix = Math.floor(x), iy = Math.floor(y), iz = Math.floor(z);
  let fx = x - ix, fy = y - iy, fz = z - iz;
  fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy); fz = fz * fz * (3 - 2 * fz);
  const a = mix(mix(ihash(ix, iy, iz), ihash(ix + 1, iy, iz), fx), mix(ihash(ix, iy + 1, iz), ihash(ix + 1, iy + 1, iz), fx), fy);
  const b = mix(mix(ihash(ix, iy, iz + 1), ihash(ix + 1, iy, iz + 1), fx), mix(ihash(ix, iy + 1, iz + 1), ihash(ix + 1, iy + 1, iz + 1), fx), fy);
  return mix(a, b, fz);
};

// ---- driver ------------------------------------------------------------
// (a) 20 draws from the default seed, exactly as the page loads it
for (let i = 0; i < 20; i++) console.log("a " + rnd());
// (b) the rseed(3) pattern (a named generator system's stream)
_seed = (20261110 + Math.imul(3, 7919)) | 0;
for (let i = 0; i < 10; i++) console.log("b " + rnd());
// (c) the z=0 slice of the original 3D value noise == the 2D port
for (const [x, y] of [[0.3, 7.9], [-12.4, 3.1], [25.0, -8.2], [4.7, 4.7], [0.0, 0.0]])
  console.log("c " + vnoise(x, y, 0));
