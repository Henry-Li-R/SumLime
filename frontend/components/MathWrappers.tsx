export function MathInline(props: any) {
  const tex = props["data-tex"] ?? "";
  return (
    <span
      className="group relative inline-flex items-baseline cursor-pointer"
      onClick={() => navigator.clipboard.writeText(tex)}
      title="Copy LaTeX"
    >
      <span className="katex-wrapper">{props.children}</span>
    </span>
  );
}

export function MathBlock(props: any) {
  const tex = props["data-tex"] ?? "";
  return (
    <div
      className="group relative my-2 cursor-pointer"
      onClick={() => navigator.clipboard.writeText(tex)}
      title="Copy LaTeX"
    >
      <div className="katex-wrapper overflow-x-auto">{props.children}</div>
    </div>
  );
}