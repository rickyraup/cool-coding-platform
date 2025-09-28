/// <reference types="react" />
/// <reference types="react-dom" />

declare global {
  namespace JSX {
    interface Element extends React.ReactElement<unknown, unknown> {}
    interface IntrinsicElements {
      [elemName: string]: unknown;
    }
  }
}

export {};