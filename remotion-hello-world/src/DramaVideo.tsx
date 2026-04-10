import React, { useMemo, useState, useEffect } from 'react';
import {
    AbsoluteFill,
    Audio,
    Sequence,
    staticFile,
    useCurrentFrame,
    useVideoConfig,
    interpolate,
    spring,
    continueRender,
    delayRender
} from 'remotion';

// --- 결정론적 랜덤 (Deterministic Random) 유틸리티 ---
const pseudoRandom = (seed: number) => {
    const x = Math.sin(seed) * 10000;
    return x - Math.floor(x);
};

// --- SRT 파서 ---
const srtParser = (content: string) => {
    if (!content) return [];
    const regex = /(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]+?)(?=\n{2,}|\n*$)/g;
    const items = [];
    let match;
    while ((match = regex.exec(content)) !== null) {
        const [, id, startStr, endStr, fullText] = match;
        const toSeconds = (time: string) => {
            const [hh, mm, ss] = time.split(':');
            const [s, ms] = ss.split(',');
            return parseInt(hh) * 3600 + parseInt(mm) * 60 + parseInt(s) + parseInt(ms) / 1000;
        };
        const start = toSeconds(startStr);
        const end = toSeconds(endStr);
        const text = fullText.trim().replace(/\n/g, ' ');

        const parts = text.split(',').map(p => p.trim()).filter(p => p);
        if (parts.length > 1) {
            const duration = end - start;
            const totalChars = parts.join('').length;
            let currentStart = start;

            parts.forEach((part, index) => {
                const partDuration = (part.length / totalChars) * duration;
                const partEnd = (index === parts.length - 1) ? end : currentStart + partDuration;
                items.push({
                    id: parseInt(id) * 100 + index,
                    start: currentStart,
                    end: partEnd,
                    text: part + (index < parts.length - 1 ? ',' : ''),
                });
                currentStart = partEnd;
            });
        } else {
            items.push({
                id: parseInt(id),
                start,
                end,
                text,
            });
        }
    }
    return items;
};

// --- 폰트 및 스타일 전역 설정 ---
const FONT_JUA = staticFile('fonts/Jua-Regular.ttf');
const FONT_DOHYEON = staticFile('fonts/DoHyeon-Regular.ttf');
const FONT_NOTOSANS = staticFile('fonts/NotoSansKR-VariableFont_wght.ttf');

// --- 시네마틱 효과 컴포넌트 ---
const CinematicOverlay: React.FC = () => {
    const frame = useCurrentFrame();
    const flicker = useMemo(() => {
        const noise = Math.sin(frame * 0.5) * 0.3 + Math.sin(frame * 1.2) * 0.2 + pseudoRandom(frame) * 0.5;
        return 0.96 + (Math.abs(noise) % 0.04);
    }, [frame]);

    return (
        <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 100 }}>
            <AbsoluteFill style={{
                backgroundColor: 'white',
                opacity: 1 - flicker,
            }} />
        </AbsoluteFill>
    );
};

// --- 이미지 시네마틱 애니메이션 컴포넌트 (강력한 랜덤성 적용) ---
const AnimatedImage: React.FC<{ src: string, index: number, duration: number }> = ({ src, index, duration }) => {
    const frame = useCurrentFrame();

    // index를 기반으로 매번 다른 애니메이션 패턴 생성
    const motionData = useMemo(() => {
        const seed = index * 543.21;
        const random1 = pseudoRandom(seed);
        const random2 = pseudoRandom(seed + 1);
        const random3 = pseudoRandom(seed + 2);
        const random4 = pseudoRandom(seed + 3);

        const zoomIn = random1 > 0.5;
        const startScale = zoomIn ? 1.1 + (random2 * 0.1) : 1.4 + (random2 * 0.1);
        let endScale = zoomIn ? startScale + 0.25 : startScale - 0.25;

        // [추가] 3장마다 부여되는 특별 효과 (교차 적용)
        let effectType: 'none' | 'flash' | 'fast_zoom' | 'high_contrast' | 'bw' = 'none';
        if ((index + 1) % 3 === 0) {
            const effects: ('flash' | 'fast_zoom' | 'high_contrast' | 'bw')[] = ['flash', 'fast_zoom', 'high_contrast', 'bw'];
            effectType = effects[Math.floor(index / 3) % effects.length];
        }

        if (effectType === 'fast_zoom') {
            endScale = zoomIn ? startScale + 0.8 : startScale - 0.8;
        }

        const movePatterns = [
            { x: [-100, 100], y: [-50, 50] },
            { x: [100, -100], y: [50, -50] },
            { x: [0, 0], y: [-150, 150] },
            { x: [-150, 150], y: [0, 0] },
            { x: [-80, -80], y: [-80, 80] },
            { x: [120, -120], y: [-120, 120] },
        ];
        const pattern = movePatterns[Math.floor(random3 * movePatterns.length)];

        return {
            startScale,
            endScale,
            xRange: pattern.x,
            yRange: pattern.y,
            blurIn: random4 > 0.7,
            effectType
        };
    }, [index]);

    const progress = frame / duration;

    // 이징(Easing) 적용: fast_zoom일 경우 가속도 추가
    const progressEased = motionData.effectType === 'fast_zoom'
        ? Math.pow(progress, 1.5)
        : progress;

    const scale = interpolate(progressEased, [0, 1], [motionData.startScale, motionData.endScale]);
    const translateX = interpolate(progressEased, [0, 1], motionData.xRange);
    const translateY = interpolate(progressEased, [0, 1], motionData.yRange);

    const opacity = interpolate(progress, [0, 0.1, 0.9, 1], [0, 1, 1, 0]);
    const blur = motionData.blurIn
        ? interpolate(progress, [0, 0.15, 0.85, 1], [15, 0, 0, 15], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
        : 0;

    // 특별 효과 스타일 계산
    const filterStyle = useMemo(() => {
        let filters = `blur(${blur}px)`;
        if (motionData.effectType === 'bw') filters += ' grayscale(100%)';
        if (motionData.effectType === 'high_contrast') filters += ' contrast(180%) brightness(120%)';
        return filters;
    }, [blur, motionData.effectType]);

    const flashOpacity = motionData.effectType === 'flash'
        ? interpolate(progress, [0, 0.1, 0.2], [0, 0.6, 0], { extrapolateRight: 'clamp' })
        : 0;

    return (
        <AbsoluteFill style={{ backgroundColor: 'black', overflow: 'hidden', opacity }}>
            <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: `translate(-50%, -50%)`,
                width: '1080px',
                height: '1080px',
            }}>
                <img
                    src={staticFile(`images/${src}`)}
                    style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
                        filter: filterStyle,
                    }}
                />
                {/* 화이트 플래시 효과 레이어 */}
                <AbsoluteFill style={{ backgroundColor: 'white', opacity: flashOpacity, pointerEvents: 'none' }} />
            </div>
        </AbsoluteFill>
    );
};

// --- 키워드 팝업 컴포넌트 ---
const KeywordPopup: React.FC<{ text: string, index: number }> = ({ text, index }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const springValue = spring({
        frame,
        fps,
        config: { mass: 0.6, stiffness: 180, damping: 10 },
    });

    const scale = interpolate(springValue, [0, 0.4, 1], [0.5, 1.35, 1]);
    const opacity = interpolate(frame, [0, 10, 80, 90], [0, 1, 1, 0]);
    const translateY = interpolate(springValue, [0, 1], [60, 0]);

    const positions = [
        { top: '25%', left: '15%' },
        { top: '35%', right: '15%' },
        { top: '55%', left: '10%' },
        { top: '45%', right: '10%' },
        { bottom: '25%', left: '20%' },
        { bottom: '40%', right: '20%' },
    ];
    const pos = positions[index % positions.length];
    const rotate = interpolate(springValue, [0, 0.6, 1], [index % 2 === 0 ? -12 : 12, index % 2 === 0 ? 6 : -6, 0]);

    return (
        <div style={{
            position: 'absolute',
            ...pos,
            zIndex: 1000,
            pointerEvents: 'none',
            display: 'flex',
            flexDirection: 'column',
            alignItems: index % 2 === 0 ? 'flex-start' : 'flex-end',
            transform: `translateY(${translateY}px) scale(${scale}) rotate(${rotate}deg)`,
            opacity,
        }}>
            <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(12px)',
                width: '110px',
                height: '110px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                borderRadius: '50%',
                color: '#000',
                fontSize: '34px',
                fontWeight: '900',
                boxShadow: '0 10px 30px rgba(0,0,0,0.25)',
                fontFamily: 'JuaCustom, sans-serif',
                position: 'relative',
                border: '1.5px solid rgba(0,0,0,0.05)',
            }}>
                {text}
            </div>
        </div>
    );
};

interface SFXPoint {
    timestamp: number;
    sfx_file: string;
    reason: string;
}

const Scene: React.FC<{
    src: string,
    index: number,
    duration: number,
    trimStart?: number,
    trimEnd?: number
}> = ({ src, index, duration, trimStart, trimEnd }) => {
    return <AnimatedImage src={src} index={index} duration={duration} />;
};

export const DramaVideo: React.FC = () => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();
    const currentTime = frame / fps;

    const [metadata, setMetadata] = useState<{
        title: string,
        audio_file: string,
        images: any[],
        style?: {
            title?: {
                topPart?: { fontSize?: string, color?: string, backgroundColor?: string },
                bottomPart?: { fontSize?: string, color?: string }
            },
            subtitle?: { fontSize?: string, color?: string, bottom?: string | number }
        }
    }>({
        title: '',
        audio_file: 'latest_drama.wav',
        images: []
    });
    const [srtContent, setSrtContent] = useState<string>('');
    const [handle] = useState(() => delayRender());

    useEffect(() => {
        Promise.all([
            fetch(staticFile('latest_drama.srt')).then(res => res.text()),
            fetch(staticFile('metadata.json') + `?t=${Date.now()}`).then(res => res.json()),
        ]).then(([srt, meta]) => {
            setSrtContent(srt);
            setMetadata(meta);
            continueRender(handle);
        }).catch(err => {
            console.error("데이터 로드 실패:", err);
            continueRender(handle);
        });
    }, [handle]);

    const subtitles = useMemo(() => srtParser(srtContent), [srtContent]);
    const activeSubtitle = subtitles.find(s => currentTime >= s.start && currentTime <= s.end);
    const imageList = metadata?.images || [];

    // --- 스타일 설정 추출 ---
    const titleStyle = metadata?.style?.title;
    const subtitleStyle = metadata?.style?.subtitle;

    // 자막 설정 (metadata 기반)
    const subtitleFontSize = Number((subtitleStyle?.fontSize as string)?.replace('px', '')) || 46;
    const subtitleColor = (subtitleStyle?.color as string) || 'white';
    const subtitleBottom = Number(subtitleStyle?.bottom) || 350;

    // 제목 설정 (metadata 기반)
    const titleTopFontSize = Number((titleStyle?.topPart?.fontSize as string)?.replace('px', '')) || 48;
    const titleTopColor = (titleStyle?.topPart?.color as string) || 'black';
    const titleTopBg = (titleStyle?.topPart?.backgroundColor as string) || 'white';
    const titleBottomFontSize = Number((titleStyle?.bottomPart?.fontSize as string)?.replace('px', '')) || 110;
    const titleBottomColor = (titleStyle?.bottomPart?.color as string) || '#FF00FF';

    return (
        <AbsoluteFill style={{
            backgroundColor: 'black',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
        }}>
            <style>
                {`
                @font-face { font-family: 'JuaCustom'; src: url('${FONT_JUA}') format('truetype'); }
                @font-face { font-family: 'DoHyeonCustom'; src: url('${FONT_DOHYEON}') format('truetype'); }
                @font-face { font-family: 'NotoSansCustom'; src: url('${FONT_NOTOSANS}') format('truetype'); }
                `}
            </style>

            {(() => {
                const totalFrames = durationInFrames;
                const imageCount = imageList.length;
                if (imageCount === 0) return null;

                const framesPerImage = totalFrames / imageCount;

                return imageList.map((item: any, i: number) => {
                    const src = typeof item === 'object' ? item.name : item;
                    const startFrame = Math.floor(i * framesPerImage);
                    const endFrame = Math.floor((i + 1) * framesPerImage);
                    const sceneDuration = endFrame - startFrame;

                    return (
                        <Sequence key={`scene-${i}-${src}`} from={startFrame} durationInFrames={sceneDuration}>
                            <Scene src={src} index={i} duration={sceneDuration} />
                        </Sequence>
                    );
                });
            })()}

            {/* --- 상하 블랙 마스킹 --- */}
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '420px', backgroundColor: 'black', zIndex: 500 }} />
            <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: '420px', backgroundColor: 'black', zIndex: 500 }} />

            <Sequence from={0}><CinematicOverlay /></Sequence>
            <AbsoluteFill style={{ boxShadow: 'inset 0 0 150px rgba(0,0,0,0.5)', pointerEvents: 'none', zIndex: 600 }} />

            <Sequence from={0} layout="none">
                {metadata.audio_file && <Audio src={staticFile(metadata.audio_file)} />}
            </Sequence>

            <Sequence from={0} layout="none">
                {Array.from({ length: Math.ceil(durationInFrames / (fps * 10)) }).map((_, i) => {
                    const startFrame = i * 10 * fps;
                    const text = i % 2 === 0 ? '구독' : '좋아요';
                    return (
                        <Sequence from={startFrame} durationInFrames={fps * 3} key={`loop-${i}`} layout="none">
                            <KeywordPopup text={text} index={i} />
                        </Sequence>
                    );
                })}
            </Sequence>

            {/* 자막 레이어 */}
            {activeSubtitle && (
                <div style={{
                    position: 'absolute',
                    bottom: subtitleBottom,
                    width: '100%',
                    display: 'flex',
                    justifyContent: 'center',
                    padding: '0 50px',
                    zIndex: 2000,
                }}>
                    <div style={{
                        color: subtitleColor,
                        fontSize: `${subtitleFontSize}px`,
                        fontWeight: 'bold',
                        textAlign: 'center',
                        maxWidth: '92%',
                        lineHeight: '1.4',
                        textShadow: '0 2px 10px rgba(0,0,0,0.8)',
                        fontFamily: 'NotoSansCustom',
                    }}>
                        {activeSubtitle.text}
                    </div>
                </div>
            )}

            <div style={{
                position: 'absolute', top: 250, left: 0, width: '100%', transform: 'translateY(-50%)', zIndex: 3000, display: 'flex', flexDirection: 'column', alignItems: 'center', fontFamily: 'DoHyeonCustom',
            }}>
                {(() => {
                    const titleRaw = metadata?.title || '';
                    const titleParts = titleRaw.split('\n');
                    let topPart = titleParts[0];
                    let bottomPart = titleParts[1] || '';
                    if (!bottomPart && topPart.includes(' ')) {
                        const words = topPart.split(' ');
                        bottomPart = words.pop() || '';
                        topPart = words.join(' ');
                    }
                    return (
                        <>
                            <div style={{
                                backgroundColor: titleTopBg,
                                color: titleTopColor,
                                fontSize: `${titleTopFontSize}px`,
                                padding: '5px 25px',
                                borderRadius: '4px',
                                marginBottom: '15px',
                                fontWeight: 'bold',
                                border: '3px solid white',
                                boxShadow: '0 4px 15px rgba(0,0,0,0.3)',
                                letterSpacing: '-1px'
                            }}>
                                {topPart}
                            </div>
                            <div style={{
                                color: titleBottomColor,
                                fontSize: `${titleBottomFontSize}px`,
                                fontWeight: '900',
                                letterSpacing: '-4px',
                                textShadow: '0 4px 15px rgba(0,0,0,0.5)',
                                marginTop: '-10px'
                            }}>
                                {bottomPart}
                            </div>
                        </>
                    );
                })()}
            </div>
        </AbsoluteFill>
    );
};
