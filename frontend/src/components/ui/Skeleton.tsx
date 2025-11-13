import React from 'react';

interface SkeletonProps { height?: number | string; width?: number | string; className?: string; }

export function Skeleton({ height = 16, width = '100%', className = '' }: SkeletonProps) {
  return <div style={{ height, width }} className={`skeleton rounded-md ${className}`} />;
}