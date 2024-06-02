precision highp float;
precision highp int;

uniform float iIndex;
uniform vec4 iViewport; // x, y, w, h

attribute vec3 position;
attribute vec2 uv;

varying vec2 vUv;

void main() {
  vUv = uv;

  // Transform to viewport
  gl_Position = vec4(
    2.0 * (position.x - iViewport.x) / iViewport.z - 1.0,
    2.0 * (position.y - iViewport.y) / iViewport.w - 1.0,
    iIndex / 1024.0,
    1.0
  );
}
