import React from "react";
import { Composition, staticFile } from "remotion";
import { HelloWorld } from "./HelloWorld";
import { Logo, myCompSchema2 } from "./HelloWorld/Logo";
import { NewsVideo } from "./NewsVideo";
import { DramaVideo } from "./DramaVideo";
import { VideoTrimmer } from "./VideoTrimmer";

// SRT에서 마지막 시간을 추출하는 유틸리티
const getDurationFromSrt = async (fileName: string) => {
  try {
    const response = await fetch(staticFile(fileName));
    if (!response.ok) throw new Error(`SRT file not found: ${fileName}`);
    const text = await response.text();

    // 마지막 타임스탬프 (종료 시간) 추출
    const matches = Array.from(text.matchAll(/--> (\d{2}:\d{2}:\d{2},\d{3})/g));
    if (matches.length > 0) {
      const lastTime = matches[matches.length - 1][1];
      const [hh, mm, ss] = lastTime.split(':');
      const [s, ms] = ss.split(',');
      return parseInt(hh) * 3600 + parseInt(mm) * 60 + parseInt(s) + parseInt(ms) / 1000;
    }
  } catch (e) {
    console.warn("SRT duration calculation failed for", fileName, ":", e);
  }
  return 0;
};

import { DoubleTap } from "./DoubleTap";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DoubleTap"
        component={DoubleTap}
        durationInFrames={60}
        fps={30}
        width={1080}
        height={1080}
      />
      <Composition
        id="HelloWorld"
        component={HelloWorld}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
      />

      <Composition
        id="OnlyLogo"
        component={Logo}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        schema={myCompSchema2}
        defaultProps={{
          logoColor1: "#91dAE2" as const,
          logoColor2: "#86A8E7" as const,
        }}
      />
      <Composition
        id="SemiconductorNews"
        component={NewsVideo}
        calculateMetadata={async () => {
          const durationSeconds = await getDurationFromSrt("final_promo_refined.srt");
          const totalFrames = Math.ceil(durationSeconds * 30) + 30; // 1초 여유
          return {
            durationInFrames: totalFrames > 30 ? totalFrames : 150, // 최소 5초
          };
        }}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="JunkyardDrama"
        component={DramaVideo}
        calculateMetadata={async () => {
          const durationSeconds = await getDurationFromSrt("latest_drama.srt");
          const totalFrames = Math.ceil(durationSeconds * 30) + 30; // 1초 여유
          return {
            durationInFrames: totalFrames > 30 ? totalFrames : 150,
          };
        }}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="VideoAudition"
        component={VideoTrimmer}
        durationInFrames={30 * 50} // 50 seconds total
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
