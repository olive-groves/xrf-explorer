import * as THREE from 'three';
import { Ref } from 'vue';

export type Layer = {
    image: string,
    mesh: THREE.Mesh,
    uniform: LayerUniform,

}

export type LayerUniform = {
    iTime: { value: number },
    iResolution: { value: THREE.Vector3 },
    iViewport: { value: THREE.Vector4 },
    tImage: { value: THREE.Texture, type: 't' }
}

export type ToolState = {
    movementSpeed: number[],
    scrollSpeed: number[]
}