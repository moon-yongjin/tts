import React, { useMemo, useState, useEffect } from 'react';
import { AbsoluteFill, Audio, Img, Video, Sequence, staticFile, useCurrentFrame, useVideoConfig, interpolate, spring, continueRender, delayRender } from 'remotion';

// --- SRT 파서 ---
const parseSRT = (content: string) => {
    const regex = /(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]+?)(?=\n{2,}|\n*$)/g;
    const items = [];
    let match;
    while ((match = regex.exec(content)) !== null) {
        const [, id, start, end, text] = match;
        const toSeconds = (time: string) => {
            const [hh, mm, ss] = time.split(':');
            const [s, ms] = ss.split(',');
            return parseInt(hh) * 3600 + parseInt(mm) * 60 + parseInt(s) + parseInt(ms) / 1000;
        };
        items.push({
            id: parseInt(id),
            start: toSeconds(start),
            end: toSeconds(end),
            text: text.trim().replace(/\n/g, ' '),
        });
    }
    return items;
};

// --- 에셋 가져오기 유틸 ---
const TOTAL_ASSETS = 47;
const videoScenes = [8, 19]; // 비디오가 있는 장면 번호

const getAsset = (index: number) => {
    const sceneNum = (index % TOTAL_ASSETS) + 1;
    const isVideo = videoScenes.includes(sceneNum);
    const fileName = isVideo
        ? `비디오_장면_${sceneNum}.mp4`
        : `2026-2027 반도체 시장 격변과 소비자 대응 전략_장면_${String(sceneNum).padStart(2, '0')}.png`;

    return {
        path: staticFile(`images/${fileName}`),
        isVideo
    };
};

// --- 폰트 및 스타일 전역 설정 ---
const FONT_JUA = staticFile('fonts/Jua-Regular.ttf');

// --- 키워드 팝업 컴포넌트 (둥근 말풍선 스타일 + 쫀득한 띠용 애니메이션) ---
const KeywordPopup: React.FC<{ text: string, index: number }> = ({ text, index }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // 찰진 튕김을 위한 스프링 설정 (Damping 낮춰서 여운이 남게 함)
    const springValue = spring({
        frame,
        fps,
        config: { mass: 0.6, stiffness: 180, damping: 10 },
    });

    // 1.0 -> 1.35 -> 1.0 느낌의 쫀득한 튕김
    const scale = interpolate(springValue, [0, 0.4, 1], [0.5, 1.35, 1]);
    const opacity = interpolate(frame, [0, 10, 80, 90], [0, 1, 1, 0]);
    const translateY = interpolate(springValue, [0, 1], [60, 0]);

    // 약간의 회전(Tilt) 추가 - 더 생동감 있게
    const rotate = interpolate(springValue, [0, 0.6, 1], [index % 2 === 0 ? -12 : 12, index % 2 === 0 ? 6 : -6, 0]);

    // 좌우 배치 및 꼬리 방향 결정
    const isLeft = index % 2 === 0;

    if (!text) return null;

    return (
        <div style={{
            position: 'absolute',
            top: isLeft ? '35%' : '45%',
            left: isLeft ? '10%' : 'auto',
            right: !isLeft ? '10%' : 'auto',
            zIndex: 100,
            pointerEvents: 'none',
            display: 'flex',
            flexDirection: 'column',
            alignItems: isLeft ? 'flex-start' : 'flex-end',
            transform: `translateY(${translateY}px) scale(${scale}) rotate(${rotate}deg)`,
            opacity,
        }}>
            {/* 말풍선 본체 */}
            <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(12px)',
                padding: '15px 45px',
                borderRadius: '55px',
                color: '#000',
                fontSize: '54px',
                fontWeight: '900',
                boxShadow: '0 15px 45px rgba(0,0,0,0.3)',
                fontFamily: 'JuaCustom, sans-serif', // 형님이 주신 Jua 폰트 적용
                whiteSpace: 'nowrap',
                position: 'relative',
                border: '2px solid rgba(255,255,255,0.4)',
            }}>
                {text}

                {/* 말풍선 꼬리 */}
                <div style={{
                    position: 'absolute',
                    bottom: '-15px',
                    [isLeft ? 'left' : 'right']: '50px',
                    width: '0',
                    height: '0',
                    borderLeft: '18px solid transparent',
                    borderRight: '18px solid transparent',
                    borderTop: '20px solid rgba(255, 255, 255, 0.95)',
                }} />
            </div>
        </div>
    );
};

interface SFXPoint {
    timestamp: number;
    sfx_file: string;
    reason: string;
    highlight_text?: string;
}

export const NewsVideo: React.FC = () => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();
    const currentTime = frame / fps;

    const [srtContent, setSrtContent] = useState<string>('');
    const [sfxConfig, setSfxConfig] = useState<SFXPoint[]>([]);
    const [handle] = useState(() => delayRender());

    useEffect(() => {
        // SRT와 SFX 설정을 함께 로드
        Promise.all([
            fetch(staticFile('final_promo_refined.srt')).then(res => res.text()),
            fetch(staticFile('sfx_config_news.json')).then(res => res.json())
        ]).then(([srt, sfx]) => {
            setSrtContent(srt);
            setSfxConfig(sfx);
            continueRender(handle);
        }).catch(err => {
            console.error("데이터 로드 실패:", err);
            continueRender(handle);
        });
    }, [handle]);

    const subtitles = useMemo(() => parseSRT(srtContent), [srtContent]);

    // 현재 시간에 맞는 자막 찾기
    const activeSubtitle = subtitles.find(s => currentTime >= s.start && currentTime <= s.end);

    // --- 싱크 로직: 전체 시간을 이미지 장수로 정확히 1/N 배분 ---
    const assetIndex = Math.floor((frame / durationInFrames) * TOTAL_ASSETS);
    const { path, isVideo } = getAsset(assetIndex);

    // --- 타이틀 애니메이션 (화면 끝까지 와따가따 + 10초마다 3초간 띠용) ---
    // 1. 화면 끝까지 부드럽게 와따가따 (15초 주기)
    // 1080px 너비에서 좌우 패딩 50px씩 제외하고 글자 폭 고려해서 약 700px 정도 이동
    const swayX = interpolate(
        Math.sin(frame / (fps * 2.5)),
        [-1, 1],
        [0, 680]
    );

    // 2. 10초마다 3초간 부드럽게 튕김
    const bounce = spring({
        frame: frame % (fps * 10),
        fps,
        config: {
            mass: 3.5,
            stiffness: 30,
            damping: 12,
        },
    });
    const titleScale = interpolate(bounce, [0, 0.2, 0.5, 1], [1, 1.25, 0.97, 1]);

    return (
        <AbsoluteFill style={{
            backgroundColor: 'black',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif' // 기본 시스템 폰트(자막용)
        }}>
            {/* Jua 폰트 정의 (말풍선 전용) */}
            <style>
                {`
                @font-face {
                    font-family: 'JuaCustom';
                    src: url('${FONT_JUA}') format('truetype');
                }
                `}
            </style>

            {/* 오디오 레이어 */}
            <Audio src={staticFile('final_promo_refined.wav')} />
            <Audio src={staticFile('bgm/Tense.mp3')} volume={0.12} loop />

            {/* AI 효과음 및 키워드 팝업 디렉터 (sfx_config.json 기반) */}
            {sfxConfig.map((sfx, i) => {
                const startFrame = Math.floor(sfx.timestamp * fps);
                return (
                    <React.Fragment key={i}>
                        {/* 효과음 */}
                        <Sequence from={startFrame - 1} durationInFrames={fps * 2}>
                            <Audio
                                src={staticFile(`sfx/${sfx.sfx_file}`)}
                                volume={sfx.sfx_file === 'cinematic_boom.mp3' ? 0.6 : 0.35}
                            />
                        </Sequence>
                        {/* 키워드 강조 (소리와 함께 3초간 등장) - 여기에는 Jua 적용됨 */}
                        {sfx.highlight_text && (
                            <Sequence from={startFrame} durationInFrames={fps * 3}>
                                <KeywordPopup text={sfx.highlight_text} index={i} />
                            </Sequence>
                        )}
                    </React.Fragment>
                );
            })}

            {/* 배경 에셋 (이미지 또는 비디오) */}
            <AbsoluteFill>
                {isVideo ? (
                    <Video
                        src={path}
                        style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                        }}
                        muted
                    />
                ) : (
                    <Img
                        src={path}
                        style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                            transform: `scale(${interpolate(frame % (fps * 5), [0, fps * 5], [1.05, 1.15])})`,
                        }}
                    />
                )}
            </AbsoluteFill>

            {/* 오버레이 (비네트 효과) */}
            <AbsoluteFill style={{
                boxShadow: 'inset 0 0 200px rgba(0,0,0,0.5)',
                background: 'linear-gradient(rgba(0,0,0,0) 60%, rgba(0,0,0,0.8) 100%)'
            }} />

            {/* 자막 디자인 */}
            {activeSubtitle && (
                <div style={{
                    position: 'absolute',
                    bottom: 70,
                    width: '100%',
                    display: 'flex',
                    justifyContent: 'center',
                    padding: '0 50px'
                }}>
                    <div style={{
                        backgroundColor: 'rgba(0, 0, 0, 0.5)',
                        padding: '18px 40px',
                        borderRadius: '5px',
                        color: 'white',
                        fontSize: '46px',
                        fontWeight: 'bold',
                        textAlign: 'center',
                        maxWidth: '92%',
                        lineHeight: '1.4',
                        borderLeft: '10px solid #cc0000',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.5)'
                    }}>
                        {activeSubtitle.text}
                    </div>
                </div>
            )}

            {/* 헤드라인 태그 */}
            <div style={{
                position: 'absolute',
                top: 50,
                left: 50,
                backgroundColor: '#cc0000',
                color: 'white',
                padding: '10px 25px',
                fontSize: '28px',
                fontWeight: '900',
                borderRadius: '5px',
                boxShadow: '0 5px 15px rgba(0,0,0,0.3)',
                transform: `translateX(${swayX}px) scale(${titleScale})`, // 와따가따 + 띠용 적용
                transformOrigin: 'left center'
            }}>
                2026-2027 반도체 시장 리포트
            </div>
        </AbsoluteFill>
    );
};
