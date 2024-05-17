precision highp float;
precision highp int;

uniform sampler2D tImage;
uniform vec2 uMouse; 
uniform float uRadius;
uniform bool uLensOn;

varying vec2 vUv;

void main() {
  if (!uLensOn) {
    gl_FragColor = texture2D(tImage, vUv);
  } else {
    vec4 color = texture2D(tImage, vUv);
    
    // Calculate distance from pixel to mouse position
    float distance = distance(gl_FragCoord.xy, uMouse);
    
    if (distance <= uRadius) {
      gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
    } else {
      // Transparent outside the circle
      gl_FragColor = color;
    }
  }
}
