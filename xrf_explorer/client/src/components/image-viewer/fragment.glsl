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
uniform float uOpacity;
uniform float uContrast;
uniform float uSaturation;

varying vec2 vUv;

// Convert RGB to HSL
vec3 rgbToHsl(vec3 rgb) {
    vec3 hsl;
    float maxVal = max(max(rgb.r, rgb.g), rgb.b);
    float minVal = min(min(rgb.r, rgb.g), rgb.b);
    float delta = maxVal - minVal;

    hsl.z = (maxVal + minVal) * 0.5;

    if (delta < 1e-5) {
        hsl.x = 0.0;
        hsl.y = 0.0;
    } else {
        hsl.y = delta / (1.0 - abs(2.0 * hsl.z - 1.0));
        if (maxVal == rgb.r) {
            hsl.x = mod((rgb.g - rgb.b) / delta, 6.0);
        } else if (maxVal == rgb.g) {
            hsl.x = ((rgb.b - rgb.r) / delta) + 2.0;
        } else {
            hsl.x = ((rgb.r - rgb.g) / delta) + 4.0;
        }
        hsl.x *= 60.0;
    }

    return hsl;
}

// Convert HSL to RGB
vec3 rgbFromHsl(vec3 hsl) {
    float c = (1.0 - abs(2.0 * hsl.z - 1.0)) * hsl.y;
    float x = c * (1.0 - abs(mod(hsl.x / 60.0, 2.0) - 1.0));
    float m = hsl.z - 0.5 * c;

    vec3 rgb;
    if (hsl.x < 60.0) {
        rgb = vec3(c, x, 0.0);
    } else if (hsl.x < 120.0) {
        rgb = vec3(x, c, 0.0);
    } else if (hsl.x < 180.0) {
        rgb = vec3(0.0, c, x);
    } else if (hsl.x < 240.0) {
        rgb = vec3(0.0, x, c);
    } else if (hsl.x < 300.0) {
        rgb = vec3(x, 0.0, c);
    } else {
        rgb = vec3(c, 0.0, x);
    }

    return rgb + m;
}
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

  // Apply contrast
  gl_FragColor.rgb = ((gl_FragColor.rgb - 0.5) * max(uContrast, 0.0)) + 0.5;

  // Apply saturation
  vec3 hslColor = rgbToHsl(gl_FragColor.rgb);
  hslColor.y *= uSaturation;
  gl_FragColor.rgb = rgbFromHsl(hslColor);

  // Apply opacity
  gl_FragColor = vec4(gl_FragColor.xyz, gl_FragColor.w * uOpacity);
}
