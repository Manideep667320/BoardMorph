import React from 'react';
import { BaseEdge, getBezierPath } from '@xyflow/react';
import type { EdgeProps } from '@xyflow/react';

export const AnimatedFlowEdge: React.FC<EdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const isActive = Boolean(data?.isActive);
  const label = data?.label as string | undefined;

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          stroke: isActive ? '#10B981' : '#94A3B8',
          strokeWidth: isActive ? 3 : 1.8,
          transition: 'stroke 0.3s ease, stroke-width 0.3s ease',
        }}
        className={isActive ? 'flow-edge-active' : ''}
      />
      {label && (
        <text
          x={labelX}
          y={labelY - 8}
          textAnchor="middle"
          className="text-[11px] font-mono fill-slate-500 bg-white px-1"
        >
          {label}
        </text>
      )}
    </>
  );
};
