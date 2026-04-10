import {
    AbsoluteFill,
    interpolate,
    spring,
    useCurrentFrame,
    useVideoConfig,
    staticFile,
} from "remotion";
import React from "react";

// @font-face 추가 (폰트 로드)
const fontFace = `
  @font-face {
    font-family: 'DoHyeon';
    src: url('${staticFile("fonts/DoHyeon-Regular.ttf")}') format('truetype');
  }
`;

export const DoubleTap: React.FC = () => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // 첫 번째 탭 (더 강력한 스프링)
    const scale1 = spring({
        frame: frame,
        fps,
        config: {
            stiffness: 300,
            damping: 15,
        },
    });

    // 두 번째 탭 (더 크게 튕기게)
    const scale2 = spring({
        frame: frame - 12, // 간격을 조금 더 좁게 (박진감)
        fps,
        config: {
            stiffness: 300,
            damping: 10,
        },
    });

    // 애니메이션 조합 (더 역동적인 스케일 변화)
    const scale = frame < 12
        ? interpolate(scale1, [0, 1], [1, 2.0])
        : interpolate(scale2, [0, 1], [1, 2.2]);

    const opacity = interpolate(frame, [0, 5, 45, 55], [0, 1, 1, 0]);

    return (
        <AbsoluteFill
            style={{
                justifyContent: "center",
                alignItems: "center",
                backgroundColor: "transparent",
            }}
        >
            <style>{fontFace}</style>
            <div
                style={{
                    transform: `scale(${scale})`,
                    opacity,
                    backgroundColor: "rgba(0, 0, 0, 0.8)",
                    padding: "50px 100px",
                    borderRadius: "150px",
                    border: "6px solid gold", // 더 고급진 골드 테두리
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: "30px",
                    boxShadow: "0 0 50px rgba(255, 215, 0, 0.5)",
                }}
            >
                {/* 하트 아이콘 (더블탭 상징) */}
                <div style={{ fontSize: "120px", filter: "drop-shadow(0 0 10px red)" }}>❤️</div>
                <div
                    style={{
                        color: "white",
                        fontSize: "100px",
                        fontWeight: "bold",
                        fontFamily: "DoHyeon, sans-serif", // 도현체 적용
                        textShadow: "4px 4px 8px rgba(0,0,0,0.8)",
                        letterSpacing: "-2px",
                    }}
                >
                    화면 두번 톡톡!
                </div>
            </div>
        </AbsoluteFill>
    );
};
