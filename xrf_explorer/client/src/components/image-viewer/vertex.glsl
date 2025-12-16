precision highp float;
precision highp int;

uniform float iIndex;
uniform vec4 iViewport;
uniform mat3 mRegister;

in vec3 position;
in vec2 uv;

out vec2 vUv;

void main() {
  vUv = uv;

  // Rotate/transform in image space
  vec3 p = mRegister * vec3(position.xy, 1.0);

  // Convert to clip space using viewport
  float px = 2.0 * (p.x - iViewport.x) / iViewport.z - 1.0;
  float py = 2.0 * (p.y - iViewport.y) / iViewport.w - 1.0;

  gl_Position = vec4(px, py, iIndex / 1024.0, 1.0);
}