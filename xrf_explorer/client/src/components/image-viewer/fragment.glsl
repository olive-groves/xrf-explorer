precision highp float;
precision highp int;

const int TRANSPARENT = 0x00;
const int WHOLE = 0x01;
const int IN_LENS = 0x02;
const int OUTSIDE_LENS = 0x03;
const vec4 transparent = vec4(0.0, 0.0, 0.0, 0.0);

uniform sampler2D tImage;
uniform vec2 uMouse; 
uniform float uRadius;
uniform int iShowLayer;

varying vec2 vUv;

void main() {
  if (iShowLayer == TRANSPARENT) 
  {
    gl_FragColor = transparent;
  }
  else if (iShowLayer == WHOLE) 
  {
    gl_FragColor = texture2D(tImage, vUv);
  }
  else if (iShowLayer == IN_LENS) 
  {
    // Eucledian distance from pixel to mouse position
    float distance = distance(gl_FragCoord.xy, uMouse);
    if (distance <= uRadius) {
      gl_FragColor = texture2D(tImage, vUv);
    } else {
      gl_FragColor = transparent;
    }
  }
  else if (iShowLayer == OUTSIDE_LENS) 
  {
    // Eucledian distance from pixel to mouse position
    float distance = distance(gl_FragCoord.xy, uMouse);
    if (distance <= uRadius) {
      gl_FragColor = transparent;
    } else {
      gl_FragColor = texture2D(tImage, vUv);
    }
  }
  else 
  {
    gl_FragColor = transparent;
  }
}
