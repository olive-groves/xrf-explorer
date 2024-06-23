precision highp float;
precision highp int;

uniform vec3 iColor;
uniform vec2 iThreshold;
uniform sampler2D tMap;

in vec2 vUv;

out vec4 fragColor;

void main() {
    fragColor = texture(tMap, vUv);
    fragColor.w = clamp((fragColor.x - iThreshold.x) / (iThreshold.y - iThreshold.x), 0.0, 1.0);
    fragColor.xyz = fragColor.w * iColor / 255.0;
}