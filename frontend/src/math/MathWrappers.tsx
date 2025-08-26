import type {ReactNode} from "react";

type MathProps = {
  children?: ReactNode;
  "data-tex"?: string;
};

export function MathInline({ children, ["data-tex"]: tex = "" }: MathProps) {
  return (
    <span
      className="group relative inline-flex items-baseline cursor-pointer"
      onClick={() => navigator.clipboard.writeText(tex)}
      title="Copy LaTeX"
    >
      <span className="katex-wrapper">{children}</span>
    </span>
  );
}

export function MathBlock({children, ["data-tex"]: tex = ""}: MathProps) {
  return (
    <div
      className="group relative my-2 cursor-pointer"
      onClick={() => navigator.clipboard.writeText(tex)}
      title="Copy LaTeX"
    >
      <div className="katex-wrapper overflow-x-auto">{children}</div>
    </div>
  );
}