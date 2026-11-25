import { useState } from 'react'
import type { GraphData, GraphNode } from '../../types'

interface Props {
  data: GraphData
  onSelect?: (id: string) => void
}

function positions(nodes: GraphNode[], center: string) {
  const others = nodes.filter((node) => node.id !== center)
  const map = new Map<string, { x: number; y: number }>()
  map.set(center, { x: 300, y: 205 })
  others.forEach((node, index) => {
    const ring = index < 8 ? 0 : 1
    const count = ring === 0 ? Math.min(8, others.length) : others.length - 8
    const positionInRing = ring === 0 ? index : index - 8
    const angle = (positionInRing / Math.max(count, 1)) * Math.PI * 2 - Math.PI / 2
    const radiusX = ring === 0 ? 170 : 245
    const radiusY = ring === 0 ? 115 : 170
    map.set(node.id, {
      x: 300 + Math.cos(angle) * radiusX,
      y: 205 + Math.sin(angle) * radiusY,
    })
  })
  return map
}

export function TransactionGraph({ data, onSelect }: Props) {
  const [selected, setSelected] = useState<string | null>(data.center)
  const points = positions(data.nodes, data.center)
  const selectedNode = data.nodes.find((node) => node.id === selected)

  return (
    <div>
      <svg viewBox="0 0 600 420" className="h-auto w-full" role="img" aria-label="Transaction neighborhood graph">
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L7,3 z" fill="#475569" />
          </marker>
          <radialGradient id="centerGlow">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
          </radialGradient>
        </defs>
        <circle cx="300" cy="205" r="100" fill="url(#centerGlow)" />
        {data.edges.map((edge, index) => {
          const from = points.get(edge.source)
          const to = points.get(edge.target)
          if (!from || !to) return null
          return (
            <line
              key={`${edge.source}-${edge.target}-${index}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke="#475569"
              strokeOpacity={0.65}
              strokeWidth={1.2}
              markerEnd="url(#arrow)"
            />
          )
        })}
        {data.nodes.map((node, nodeIndex) => {
          const point = points.get(node.id)
          if (!point) return null
          const isCenter = node.id === data.center
          return (
            <g
              key={node.id || `node-${nodeIndex}`}
              transform={`translate(${point.x}, ${point.y})`}
              className="cursor-pointer"
              onClick={() => {
                setSelected(node.id)
                onSelect?.(node.id)
              }}
            >
              <circle r={node.size + 7} fill={node.color} opacity={selected === node.id ? 0.22 : 0.08} />
              <circle
                r={node.size}
                fill={node.color}
                stroke={isCenter ? '#ffffff' : 'rgba(255,255,255,0.2)'}
                strokeWidth={isCenter ? 2 : 1}
              />
              <text
                y={node.size + 15}
                textAnchor="middle"
                fontSize="9"
                fill="#94a3b8"
                fontFamily="monospace"
              >
                {String(node.id ?? '').length > 14
                  ? `${String(node.id).slice(0, 6)}…${String(node.id).slice(-4)}`
                  : String(node.id ?? '')}
              </text>
            </g>
          )
        })}
      </svg>
      <div className="mt-2 flex flex-wrap items-center justify-center gap-4 text-[11px] text-slate-400">
        {[
          ['Illicit', '#f43f5e'],
          ['Licit', '#22c55e'],
          ['Unknown', '#64748b'],
          ['High-risk prediction', '#a855f7'],
        ].map(([label, color]) => (
          <span key={label} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
            {label}
          </span>
        ))}
      </div>
      {selectedNode && (
        <p className="mt-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2 text-xs text-slate-400">
          Selected: <span className="font-mono text-slate-200">{selectedNode.id}</span> ·{' '}
          {selectedNode.label} · risk{' '}
          {selectedNode.risk_score === null ? 'N/A' : selectedNode.risk_score.toFixed(3)}
        </p>
      )}
    </div>
  )
}
