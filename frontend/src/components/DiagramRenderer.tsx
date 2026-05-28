import type {
  AngleRelationshipDiagram,
  CoordinateGraphDiagram,
  NumberLineDiagram,
  QuestionDiagramSpec,
} from '../types/questions'

interface DiagramRendererProps {
  diagram: QuestionDiagramSpec | null
  className?: string
}

function isNumberLine(diagram: QuestionDiagramSpec): diagram is NumberLineDiagram {
  return diagram.type === 'number_line'
}

function isCoordinateGraph(diagram: QuestionDiagramSpec): diagram is CoordinateGraphDiagram {
  return diagram.type === 'coordinate_graph'
}

function isAngleRelationship(diagram: QuestionDiagramSpec): diagram is AngleRelationshipDiagram {
  return diagram.type === 'angle_relationship'
}

function asNumber(value: string | number): number {
  return typeof value === 'number' ? value : Number(value)
}

function NumberLine({ diagram }: { diagram: NumberLineDiagram }) {
  const width = 720
  const height = 180
  const pad = 54
  const min = asNumber(diagram.min)
  const max = asNumber(diagram.max)
  const span = Math.max(1, max - min)
  const xFor = (value: string | number) => pad + ((asNumber(value) - min) / span) * (width - pad * 2)
  const ticks: number[] = []
  const tickStep = diagram.ticks ?? 1
  for (let value = Math.ceil(min); value <= Math.floor(max); value += tickStep) ticks.push(value)

  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="number line diagram" className="h-full w-full">
      <line x1={pad} y1={92} x2={width - pad} y2={92} stroke="#64735f" strokeWidth={3} />
      {ticks.map(tick => (
        <g key={tick}>
          <line x1={xFor(tick)} y1={82} x2={xFor(tick)} y2={102} stroke="#64735f" strokeWidth={2} />
          <text x={xFor(tick)} y={126} textAnchor="middle" className="fill-text-muted text-[14px]">
            {tick}
          </text>
        </g>
      ))}
      {(diagram.arrows ?? []).map((arrow, index) => {
        const x1 = xFor(arrow.from)
        const x2 = xFor(arrow.to)
        const mid = (x1 + x2) / 2
        const sweep = x2 >= x1 ? 1 : 0
        return (
          <g key={`${arrow.from}-${arrow.to}-${index}`}>
            <path
              d={`M ${x1} 68 A ${Math.abs(x2 - x1) / 2} 38 0 0 ${sweep} ${x2} 68`}
              fill="none"
              stroke="#d96f5f"
              strokeWidth={3}
              markerEnd="url(#arrowhead)"
            />
            {arrow.label && (
              <text x={mid} y={34} textAnchor="middle" className="fill-coral-700 text-[15px] font-semibold">
                {arrow.label}
              </text>
            )}
          </g>
        )
      })}
      {diagram.points.map(point => (
        <g key={point.id ?? `${point.value}`}>
          <circle cx={xFor(point.value)} cy={92} r={8} fill="#5f8f6b" stroke="#ffffff" strokeWidth={3} />
          {point.label && (
            <text x={xFor(point.value)} y={62} textAnchor="middle" className="fill-sage-800 text-[14px] font-semibold">
              {point.label}: {point.value}
            </text>
          )}
        </g>
      ))}
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="7" refY="3" orient="auto">
          <path d="M0,0 L0,6 L8,3 z" fill="#d96f5f" />
        </marker>
      </defs>
    </svg>
  )
}

function CoordinateGraph({ diagram }: { diagram: CoordinateGraphDiagram }) {
  const width = 720
  const height = 420
  const pad = 58
  const xMax = Math.max(1, diagram.x_max)
  const yMax = Math.max(1, diagram.y_max)
  const xFor = (x: number) => pad + (x / xMax) * (width - pad * 2)
  const yFor = (y: number) => height - pad - (y / yMax) * (height - pad * 2)
  const xTicks = Array.from({ length: Math.min(xMax, 10) + 1 }, (_, index) => index * Math.ceil(xMax / Math.min(xMax, 10)))
    .filter((value, index, values) => value <= xMax && values.indexOf(value) === index)
  const yStep = Math.max(1, Math.ceil(yMax / 6))
  const yTicks = Array.from({ length: Math.floor(yMax / yStep) + 1 }, (_, index) => index * yStep)

  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="coordinate graph" className="h-full w-full">
      {xTicks.map(tick => (
        <line key={`x-${tick}`} x1={xFor(tick)} y1={pad} x2={xFor(tick)} y2={height - pad} stroke="#e4e7df" />
      ))}
      {yTicks.map(tick => (
        <line key={`y-${tick}`} x1={pad} y1={yFor(tick)} x2={width - pad} y2={yFor(tick)} stroke="#e4e7df" />
      ))}
      <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="#53624f" strokeWidth={3} />
      <line x1={pad} y1={height - pad} x2={pad} y2={pad} stroke="#53624f" strokeWidth={3} />
      {xTicks.map(tick => (
        <text key={`xt-${tick}`} x={xFor(tick)} y={height - 28} textAnchor="middle" className="fill-text-muted text-[13px]">
          {tick}
        </text>
      ))}
      {yTicks.map(tick => (
        <text key={`yt-${tick}`} x={pad - 16} y={yFor(tick) + 4} textAnchor="end" className="fill-text-muted text-[13px]">
          {tick}
        </text>
      ))}
      {diagram.line && (
        <g>
          <line
            x1={xFor(0)}
            y1={yFor(diagram.line.intercept ?? 0)}
            x2={xFor(xMax)}
            y2={yFor(diagram.line.slope * xMax + (diagram.line.intercept ?? 0))}
            stroke="#d96f5f"
            strokeWidth={4}
          />
          {diagram.line.label && (
            <text x={width - pad - 80} y={pad + 26} className="fill-coral-700 text-[15px] font-semibold">
              {diagram.line.label}
            </text>
          )}
        </g>
      )}
      {diagram.points.map((point, index) => (
        <g key={`${point.x}-${point.y}-${index}`}>
          <circle cx={xFor(point.x)} cy={yFor(point.y)} r={7} fill="#5f8f6b" stroke="#ffffff" strokeWidth={3} />
          {point.label && (
            <text x={xFor(point.x) + 10} y={yFor(point.y) - 10} className="fill-sage-800 text-[13px] font-semibold">
              {point.label}
            </text>
          )}
        </g>
      ))}
      {diagram.highlight && (
        <circle
          cx={xFor(diagram.highlight.x)}
          cy={yFor(diagram.highlight.y)}
          r={13}
          fill="none"
          stroke="#d96f5f"
          strokeWidth={3}
        />
      )}
      <text x={width / 2} y={height - 6} textAnchor="middle" className="fill-text-muted text-[14px]">
        {diagram.x_axis ?? 'x'}
      </text>
      <text x={16} y={height / 2} textAnchor="middle" transform={`rotate(-90 16 ${height / 2})`} className="fill-text-muted text-[14px]">
        {diagram.y_axis ?? 'y'}
      </text>
    </svg>
  )
}

function AngleRelationship({ diagram }: { diagram: AngleRelationshipDiagram }) {
  const width = 620
  const height = 300
  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="angle relationship diagram" className="h-full w-full">
      <line x1={80} y1={240} x2={540} y2={60} stroke="#53624f" strokeWidth={5} strokeLinecap="round" />
      <line x1={80} y1={60} x2={540} y2={240} stroke="#53624f" strokeWidth={5} strokeLinecap="round" />
      <circle cx={310} cy={150} r={8} fill="#5f8f6b" />
      <path d="M 205 109 A 116 116 0 0 1 415 109" fill="none" stroke="#d96f5f" strokeWidth={4} />
      <path d="M 205 191 A 116 116 0 0 0 415 191" fill="none" stroke="#d96f5f" strokeWidth={4} />
      <text x={310} y={78} textAnchor="middle" className="fill-coral-700 text-[18px] font-semibold">
        {diagram.expression_a}
      </text>
      <text x={310} y={238} textAnchor="middle" className="fill-coral-700 text-[18px] font-semibold">
        {diagram.expression_b}
      </text>
      <text x={310} y={286} textAnchor="middle" className="fill-text-muted text-[14px]">
        Vertical angles are congruent
      </text>
    </svg>
  )
}

export function DiagramRenderer({ diagram, className }: DiagramRendererProps) {
  if (!diagram) return null

  return (
    <div className={className}>
      <div className="mx-auto aspect-[16/9] w-full max-w-3xl overflow-hidden rounded-xl border border-sage-200 bg-white">
        {isNumberLine(diagram) && <NumberLine diagram={diagram} />}
        {isCoordinateGraph(diagram) && <CoordinateGraph diagram={diagram} />}
        {isAngleRelationship(diagram) && <AngleRelationship diagram={diagram} />}
      </div>
    </div>
  )
}
