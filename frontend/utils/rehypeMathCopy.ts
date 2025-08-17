import { visit } from "unist-util-visit";
import type { Root } from "hast";

function hasKatexClass(node: any): boolean {
  const cn = node?.properties?.className;
  if (Array.isArray(cn)) return cn.includes("katex");
  if (typeof cn === "string") return cn.split(/\s+/).includes("katex");
  return false;
}

function extractTexFromAnnotation(node: any): string | null {
  if (!node?.children) return null;
  for (const c of node.children) {
    if (
      c?.tagName === "annotation" &&
      c?.properties?.encoding === "application/x-tex" &&
      typeof c?.children?.[0]?.value === "string"
    ) {
      return c.children[0].value as string;
    }
    const deep = extractTexFromAnnotation(c);
    if (deep) return deep;
  }
  return null;
}

export default function rehypeMathCopy() {
  return (tree: Root) => {
    visit(tree, "element", (node: any, index: number | null | undefined, parent: any) => {
      if (!parent || typeof(index) !== "number") return;
      if (!hasKatexClass(node)) return;

      const tex = extractTexFromAnnotation(node) ?? "";

      // inline if parent is p/span, else block
      const wrapperTag =
        parent.tagName === "p" || parent.tagName === "span"
          ? "math-inline"
          : "math-block";

      const wrapper = {
        type: "element",
        tagName: wrapperTag,
        properties: { "data-tex": tex },
        children: [node],
      };

      // Replace the KaTeX node with our wrapper
      parent.children[index] = wrapper;
    });
  };
}