import React, { useEffect, useState } from 'react';
import { AbsoluteFill, Video, staticFile, Sequence, useVideoConfig, delayRender, continueRender } from 'remotion';

export const VideoTrimmer: React.FC = () => {
    const { fps } = useVideoConfig();
    const [metadata, setMetadata] = useState<any>(null);
    const [handle] = useState(() => delayRender());

    useEffect(() => {
        fetch(staticFile('metadata.json') + `?t=${Date.now()}`)
            .then(res => res.json())
            .then(data => {
                setMetadata(data);
                continueRender(handle);
            })
            .catch(err => {
                console.error("Metadata load failed", err);
                continueRender(handle);
            });
    }, [handle]);

    if (!metadata) return null;

    const scenes = metadata?.images || [];

    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            {(() => {
                let currentOffset = 0;
                return scenes.map((item: any, i: number) => {
                    const isObj = typeof item === 'object' && item !== null;
                    const src = isObj ? item.name : item;
                    const trimStart = isObj ? (item.trimStart || 0) : 0;
                    const trimEnd = isObj ? item.trimEnd : undefined;

                    if (!src || !src.toLowerCase().endsWith('.mp4')) return null;

                    // trimEnd가 지정되어 있으면 그 분량만큼, 없으면 기본 10초 노출
                    const sceneDuration = trimEnd !== undefined
                        ? (trimEnd - trimStart)
                        : 10 * fps;

                    const startFrame = currentOffset;
                    currentOffset += sceneDuration;

                    return (
                        <Sequence key={`${src}-${i}`} from={startFrame} durationInFrames={Math.max(1, sceneDuration)}>
                            <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
                                <div style={{
                                    width: 1080,
                                    height: 1080,
                                    overflow: 'hidden',
                                    position: 'relative'
                                }}>
                                    <Video
                                        src={staticFile(`images/${src}`)}
                                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                        startFrom={trimStart}
                                        endAt={trimEnd}
                                    />
                                </div>
                            </AbsoluteFill>
                        </Sequence>
                    );
                });
            })()}
        </AbsoluteFill>
    );
};
