import { visit } from "unist-util-visit";
import type { Root, Element, Parent, Properties, Node, Text } from "hast";

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null;
}

function isElement(n: unknown): n is Element {
  return isRecord(n) && n.type === "element" && typeof n.tagName === "string";
}

function isText(n: unknown): n is Text {
  return isRecord(n) && n.type === "text" && typeof n.value === "string";
}

function hasKatexClass(node: Element): boolean {
  const props = (isRecord(node.properties) ? (node.properties as Properties) : undefined);
  const cn = props?.className as unknown;
  if (Array.isArray(cn)) return cn.includes("katex");
  if (typeof cn === "string") return cn.split(/\s+/).includes("katex");
  return false;
}

function extractTexFromAnnotation(node: Node): string | null {
  if (!isElement(node) || !Array.isArray(node.children)) return null;

  for (const c of node.children) {
    if (isElement(c) && c.tagName === "annotation") {
      const props = (isRecord(c.properties) ? (c.properties as Properties) : undefined);
      if (props?.encoding === "application/x-tex") {
        const first = c.children?.[0];
        if (isText(first)) return first.value;
      }
    }
    const deep = extractTexFromAnnotation(c);
    if (deep) return deep;
  }
  return null;
}

export default function rehypeMathCopy() {
  return (tree: Root) => {
    visit(tree, "element", (node, index, parent) => {
      if (!isElement(node)) return;
      if (typeof index !== "number") return;
      if (!parent || !("children" in parent)) return;
      if (!hasKatexClass(node)) return;

      const tex = extractTexFromAnnotation(node) ?? "";
      const wrapperTag =
        (isElement(parent) && (parent.tagName === "p" || parent.tagName === "span"))
          ? "math-inline"
          : "math-block";

      const wrapper: Element = {
        type: "element",
        tagName: wrapperTag,
        properties: { "data-tex": tex },
        children: [node],
      };

      (parent as Parent).children[index] = wrapper;
    });
  };
}