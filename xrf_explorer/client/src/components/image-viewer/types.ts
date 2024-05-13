import * as THREE from 'three';

export type Layer = {
    id: string,
    image: string,
    mesh?: THREE.Mesh,
    uniform: LayerUniform
}

export type LayerUniform = {
    iIndex: { value: number },
    iViewport: { value: THREE.Vector4 },
    tImage?: { value: THREE.Texture, type: 't' },
    mRegister: { value: THREE.Matrix3 }
}

export type ToolState = {
    movementSpeed: number[],
    scrollSpeed: number[]
}