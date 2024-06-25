precision highp float;
precision highp int;

in vec3 position;
in vec2 uv;

out vec2 vUv;

void main() {
  vUv = uv;

  // Scale vertices from [0, 1] to [-1, 1]
  gl_Position = vec4(position.xy * 2.0 - 1.0, position.z, 1.0);
}