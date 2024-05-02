import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const remFactor = 16;

export function remToPx(rem: number): number {
  return rem * remFactor;
}

export function pxToRem(px: number): number {
  return px / remFactor;
}