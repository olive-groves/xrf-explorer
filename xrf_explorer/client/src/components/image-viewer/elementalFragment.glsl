// This fragment shader is used to apply intensity thresholds to the alpha channel of an image.
precision highp float;
precision highp int;

uniform vec3 iColor;
uniform vec2 iThreshold;
uniform sampler2D tMap;

in vec2 vUv;

out vec4 fragColor;

void main() {
    fragColor = texture(tMap, vUv);

    // Apply intensity thresholds to alpha channel.
    fragColor.w = clamp((fragColor.x - iThreshold.x) / (iThreshold.y - iThreshold.x), 0.0, 1.0);
    
    // Set output color as color multipied by weight (alpha)
    fragColor.xyz = fragColor.w * iColor / 255.0;
}