import {
  useCurrentFrame,
  AbsoluteFill,
  spring,
  useVideoConfig,
  staticFile,
  Img
} from 'remotion';
import React from 'react';

// --- 부품 슬라이싱 유틸리티 ---
const SpritePart = ({
  src,
  x, y, w, h, // 원본 이미지에서의 좌표/크기
  scale = 0.5,
  style = {}
}: {
  src: string, x: number, y: number, w: number, h: number, scale?: number, style?: React.CSSProperties
}) => {
  return (
    <div style={{
      width: w * scale,
      height: h * scale,
      overflow: 'hidden',
      position: 'absolute',
      ...style
    }}>
      <Img
        src={src}
        style={{
          position: 'absolute',
          left: -x * scale,
          top: -y * scale,
          width: 1024 * scale,
          height: 'auto',
          maxWidth: 'none'
        }}
      />
    </div>
  );
};

export const HelloWorld = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const characterParts = staticFile("character_parts.png");
  const handParts = staticFile("hand_parts.png");

  // 1. 애니메이션 로직
  const walkCycle = Math.sin(frame / 6);
  const bodyBob = Math.abs(walkCycle) * 10;
  const armAngle = walkCycle * 40;
  const legAngle = walkCycle * 45;

  const entrance = spring({
    frame,
    fps,
    config: { stiffness: 100, damping: 10 },
  });

  return (
    <AbsoluteFill style={{ backgroundColor: '#87CEEB', overflow: 'hidden' }}>

      {/* 바닥 (구르기 효과) */}
      <div style={{
        position: 'absolute',
        bottom: 0,
        width: '200%',
        height: '150px',
        backgroundColor: '#7cfc00',
        transform: `translateX(${-(frame * 12) % 1920}px)`,
        borderTop: '5px solid #556b2f'
      }} />

      {/* --- 캐릭터 리깅 시작 --- */}
      <div style={{
        position: 'absolute',
        left: '50%',
        top: '55%',
        transform: `translate(-50%, -50%) scale(${entrance}) translateY(${bodyBob}px)`,
      }}>

        {/* 1. 다리 (뒤쪽) */}
        <div style={{ transform: `rotate(${-legAngle}deg)`, transformOrigin: 'top center', position: 'absolute', left: 35, top: 140 }}>
          <SpritePart src={characterParts} x={630} y={170} w={150} h={400} scale={0.4} />
        </div>

        {/* 2. 몸통 (Torso) */}
        <div style={{ position: 'relative', zIndex: 10 }}>
          <SpritePart src={characterParts} x={240} y={320} w={145} h={350} scale={0.5} style={{ position: 'relative' }} />
        </div>

        {/* 3. 머리 (Head) */}
        <div style={{ position: 'absolute', top: -95, left: 18, zIndex: 11 }}>
          <SpritePart src={characterParts} x={250} y={85} w={110} h={210} scale={0.5} />
        </div>

        {/* 4. 팔 (앞쪽) */}
        <div style={{
          transform: `rotate(${armAngle}deg)`,
          transformOrigin: 'top center',
          position: 'absolute',
          left: 10,
          top: 25,
          zIndex: 12
        }}>
          <SpritePart src={characterParts} x={125} y={360} w={85} h={180} scale={0.5} />
          {/* 하완 (Lower Arm) */}
          <div style={{
            transform: `rotate(${Math.abs(armAngle) * 0.4}deg)`,
            transformOrigin: 'top center',
            position: 'absolute',
            top: 85,
            left: 0
          }}>
            <SpritePart src={characterParts} x={130} y={560} w={75} h={180} scale={0.5} />
            {/* 손 (Hand Sprite) */}
            <div style={{ position: 'absolute', top: 75, left: -5 }}>
              <SpritePart src={handParts} x={415} y={380} w={130} h={150} scale={0.3} />
            </div>
          </div>
        </div>

        {/* 5. 다리 (앞쪽) */}
        <div style={{ transform: `rotate(${legAngle}deg)`, transformOrigin: 'top center', position: 'absolute', left: 10, top: 140 }}>
          <SpritePart src={characterParts} x={630} y={170} w={150} h={400} scale={0.4} />
        </div>

      </div>

      <div style={{
        position: 'absolute',
        top: 80,
        width: '100%',
        textAlign: 'center',
        fontSize: 50,
        fontWeight: 'bold',
        color: '#fff',
        fontFamily: 'sans-serif',
        textShadow: '3px 3px 6px rgba(0,0,0,0.4)'
      }}>
        CHAR RIGGING COMPLETE 🚀🏃‍♂️
      </div>

    </AbsoluteFill>
  );
};
