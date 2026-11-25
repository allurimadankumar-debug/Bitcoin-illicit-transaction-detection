interface Props {
  matrix: number[][] | unknown
}

export function ConfusionMatrix({ matrix }: Props) {
  const values = Array.isArray(matrix) && matrix.length === 2 && matrix.every((row) => Array.isArray(row) && row.length === 2)
    ? (matrix as number[][])
    : [[0, 0], [0, 0]]
  const labels = [['True negative', 'False positive'], ['False negative', 'True positive']]
  const max = Math.max(...values.flat(), 1)

  return (
    <div className="grid grid-cols-[80px_1fr_1fr] gap-1.5 text-center text-xs">
      <div />
      <div className="pb-1 text-slate-400">Pred: licit</div>
      <div className="pb-1 text-slate-400">Pred: illicit</div>
      {values.map((row, rowIndex) => (
        <div key={rowIndex} className="contents">
          <div className="flex items-center justify-end pr-2 text-slate-400">
            {rowIndex === 0 ? 'Actual licit' : 'Actual illicit'}
          </div>
          {row.map((value, columnIndex) => (
            <div
              key={columnIndex}
              className="rounded-lg border border-white/5 px-3 py-4"
              style={{ backgroundColor: `rgba(${rowIndex === columnIndex ? '34,211,238' : '244,63,94'},${0.06 + (value / max) * 0.22})` }}
              title={labels[rowIndex][columnIndex]}
            >
              <span className="text-lg font-semibold text-white">{value.toLocaleString()}</span>
              <span className="mt-1 block text-[10px] text-slate-400">{labels[rowIndex][columnIndex]}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
