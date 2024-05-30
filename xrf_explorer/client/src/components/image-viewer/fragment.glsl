precision highp float;
precision highp int;

const int TRANSPARENT = 0x00;
const int WHOLE = 0x01;
const int IN_LENS = 0x02;
const int OUTSIDE_LENS = 0x03;
const int TYPE_IMAGE = 0x00;
const int TYPE_ELEMENTAL = 0x01;
const int TYPE_CS = 0x02;
const int TYPE_DR = 0x03;
const vec4 transparent = vec4(0.0, 0.0, 0.0, 0.0);

uniform int iLayerType;
uniform sampler2D tImage;
uniform int iAuxiliary;
uniform sampler2D tAuxiliary;
uniform vec2 uMouse; 
uniform float uRadius;
uniform int iShowLayer;
uniform float uOpacity;
uniform float uContrast;
uniform float uSaturation;
uniform float uGamma;
uniform float uBrightness;

varying vec2 vUv;

// Convert RGB to HSL
vec3 rgbToHsl(vec3 rgb) {
  vec3 hsl;
  float maxValue = max(max(rgb.r, rgb.g), rgb.b);
  float minValue = min(min(rgb.r, rgb.g), rgb.b);
  float delta = maxValue - minValue;

  hsl.z = (maxValue + minValue) * 0.5;

  if (delta < 1e-5) {
    hsl.x = 0.0; // Hue
    hsl.y = 0.0; // Saturation
  } else {
    hsl.y = delta / (1.0 - abs(2.0 * hsl.z - 1.0)); // Saturation

    if (maxValue == rgb.r) {
      hsl.x = mod((rgb.g - rgb.b) / delta, 6.0); // Hue
    } else if (maxValue == rgb.g) {
      hsl.x = ((rgb.b - rgb.r) / delta) + 2.0; // Hue
    } else {
      hsl.x = ((rgb.r - rgb.g) / delta) + 4.0; // Hue
    }
    hsl.x *= 60.0;
  }

  return hsl;
}

// Convert HSL to RGB
vec3 rgbFromHsl(vec3 hsl) {
  float chroma = (1.0 - abs(2.0 * hsl.z - 1.0)) * hsl.y;
  float intermValue = chroma * (1.0 - abs(mod(hsl.x / 60.0, 2.0) - 1.0));
  float modifier = hsl.z - 0.5 * chroma;

  vec3 rgb;
  if (hsl.x < 60.0) {
    rgb = vec3(chroma, intermValue, 0.0); // Red
  } else if (hsl.x < 120.0) {
    rgb = vec3(intermValue, chroma, 0.0); // Yellow
  } else if (hsl.x < 180.0) {
    rgb = vec3(0.0, chroma, intermValue); // Green
  } else if (hsl.x < 240.0) {
    rgb = vec3(0.0, intermValue, chroma); // Cyan
  } else if (hsl.x < 300.0) {
    rgb = vec3(intermValue, 0.0, chroma); // Blue
  } else {
    rgb = vec3(chroma, 0.0, intermValue); // Magenta
  }

  return rgb + modifier;
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

  // Modify color based on layer type
  if (iLayerType == TYPE_ELEMENTAL) {
    // Get auxiliary data from texture
    // Texture is 256x2 (wxh), we can hence sample at (channel/256, 0) for the color
    // and (channel/256, 1) for the thresholds.
    // We get the color from the auxiliary and render in alphascale.
    vec4 auxiliaryColor = texture2D(tAuxiliary, vec2(float(iAuxiliary) / 256.0, 0.0));
    vec2 threshold = texture2D(tAuxiliary, vec2(float(iAuxiliary) / 256.0, 1.0)).xy;
    if (auxiliaryColor.w == 0.0) {
      gl_FragColor = transparent;
    } else {
      float alpha = (gl_FragColor.x - threshold.x) / (threshold.y - threshold.x);
      gl_FragColor = vec4(
        auxiliaryColor.xyz,
        clamp(alpha, 0.0, 1.0)
      );
    }
  }

  // Apply contrast
  gl_FragColor.rgb = ((gl_FragColor.rgb - 0.5) * max(uContrast, 0.0)) + 0.5;

  // Create HSL color vector for brightness and saturation
  vec3 hslColor = rgbToHsl(gl_FragColor.rgb);

  // Apply brightness
  hslColor.z = hslColor.z + uBrightness;

  // Apply saturation
  hslColor.y = hslColor.y * uSaturation;

  // Revert HSL back to RGB
  gl_FragColor.rgb = rgbFromHsl(hslColor);

  // Apply opacity
  gl_FragColor = vec4(gl_FragColor.xyz, gl_FragColor.w * uOpacity);

  // Apply gamma correction
  gl_FragColor.rgb = pow(gl_FragColor.rgb, vec3(1.0/uGamma));
}
