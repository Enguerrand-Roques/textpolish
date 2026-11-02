import { Composition } from "remotion";
import { TextPolishVideo, TOTAL_FRAMES } from "./Video";

export const Root = () => (
  <Composition
    id="TextPolish"
    component={TextPolishVideo}
    durationInFrames={TOTAL_FRAMES}
    fps={30}
    width={1920}
    height={1080}
  />
);
