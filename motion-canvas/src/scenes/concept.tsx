import {makeScene2D, Circle, Txt} from '@motion-canvas/2d';
import {createRef, all, waitFor} from '@motion-canvas/core';
export default makeScene2D(function* (view) {
  const ring=createRef<Circle>();
  view.fill('#090e21');
  view.add(<><Txt text="A conceptual boundary" y={-300} fill="#f1f5ff" fontSize={64}/>
    <Circle ref={ring} size={180} stroke="#60e5db" lineWidth={8}/></>);
  yield* all(ring().size(400,2),ring().rotation(180,2));
  yield* waitFor(1);
});
