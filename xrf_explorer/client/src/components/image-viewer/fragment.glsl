precision highp float;
precision highp int;

const int TRANSPARENT = 0x00;
const int IN_LENS = 0x01;
const int OUTSIDE_LENS = 0x02;
const int WHOLE = 0x03;
const int TYPE_IMAGE = 0x00;
const int TYPE_ELEMENTAL = 0x01;
const int TYPE_CS = 0x02;
const int TYPE_DR = 0x03;
const vec4 transparent = vec4(0.0, 0.0, 0.0, 0.0);

uniform int iLayerType;
uniform sampler2D tImage;
uniform mat3 mRegister;
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

in vec2 vUv;

out vec4 fragColor;

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
  // Register the uv coordinate using the provided matrix
  vec3 uv = mRegister * vec3(vUv, 1.0);
  uv.xy = uv.xy / uv.z;
  // Return with transparency if the calculated uv coordinate falls outside of the texture
  if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) {
    return;
  }
  
  float distance = distance(gl_FragCoord.xy, uMouse);
  if (distance <= uRadius) {
    if ((iShowLayer & IN_LENS) != 0) {
      fragColor = texture(tImage, uv.xy);
    } else {
      return;
    }
  } else {
    if ((iShowLayer & OUTSIDE_LENS) != 0) {
      fragColor = texture(tImage, uv.xy);
    } else {
      return;
    }
  }

  // Modify color based on layer type
  if (iLayerType == TYPE_ELEMENTAL) {
    // Display the elemental maps.
    // The order independent blend of the maps has been calculated by elementalHelper.ts
    // tImage contains accumulated values, the sum of all color contributions and the sum of intensities.
    // tAuxiliary contains the maximum intensity values
    // Color is calculated as the weighted mean, sum of colors divided by sum of intensities.
    // Alpha is equal to the maximum alpha in the pixel as stored in tAuxiliary.
    fragColor.xyz = fragColor.xyz / fragColor.w;
    fragColor.w = texture(tAuxiliary, uv.xy).w;
  } else if (iLayerType == TYPE_CS) {
    // Get auxiliary data from texture
    // Element index j given by iAuxiliary, cluster index i given by R value
    // of current pixel in tImage/bitmask
    // Texture is 256x30 (wxh), we can hence sample at (j/256, i) to determine
    // if cluster i of element j is selected
    float clusterIndex = texture(tImage, uv.xy).g * 8.0;
    fragColor = texture(tAuxiliary, vec2(float(iAuxiliary) / 256.0, clusterIndex));
  } else if (iLayerType == TYPE_DR) {
    // the BLUE value (z) in the middle image (0 or 255) denotes if this pixel is in the embedding
    if (fragColor.z != 1.0) {
      fragColor = transparent;
      return;
    } else {
      vec4 bitmask = texture(tAuxiliary, vec2(fragColor.xy));
      fragColor = bitmask;
    }
  }

  // Apply contrast and brightness
  vec3 adjustedColor = ((fragColor.xyz - 0.5) * max(uContrast, 0.0)) + 0.5 + uBrightness;
  fragColor.xyz = clamp(adjustedColor, 0.0, 1.0);

  // Create HSL color vector for saturation
  vec3 hslColor = rgbToHsl(fragColor.xyz);

  // Apply saturation
  hslColor.y = hslColor.y * uSaturation;

  // Revert HSL back to RGB
  fragColor.xyz = rgbFromHsl(hslColor);

  // Apply gamma correction
  fragColor.xyz = pow(fragColor.xyz, vec3(1.0 / uGamma));
  
  // Apply opacity
  fragColor.w = fragColor.w * uOpacity;
}
