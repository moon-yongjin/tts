/**
 * Grok Hook - Fetch Interception Script
 * 이 스크립트는 실제 페이지 컨텍스트에서 실행되어 Grok의 fetch 요청을 가로챕니다.
 */
(function() {
    if (window.__GROK_HOOK_LOADED) return;
    window.__GROK_HOOK_LOADED = true;

    console.log('✅ Grok Hook: Fetch Interceptor Active');

    const originalFetch = window.fetch;

    window.fetch = function() {
        const url = arguments[0];
        const isConversationApi = typeof url === 'string' && url.includes('/rest/app-chat/conversations/new');

        if (!isConversationApi) {
            return originalFetch.apply(this, arguments);
        }

        return originalFetch.apply(this, arguments).then(response => {
            const clone = response.clone();
            const reader = clone.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            function processStream() {
                reader.read().then(({ done, value }) => {
                    if (value) {
                        buffer += decoder.decode(value, { stream: !done });
                        const lines = buffer.split('\n');
                        buffer = lines.pop();

                        for (const line of lines) {
                            if (!line.trim()) continue;
                            try {
                                const data = JSON.parse(line);
                                // Grok-Viewer 방식의 파싱 로직 적용
                                const streamResponse = data?.result?.response?.streamingVideoGenerationResponse;
                                if (streamResponse && streamResponse.videoUrl) {
                                    const videoUrl = streamResponse.videoUrl;
                                    // users/ 경로 처리
                                    const fullUrl = videoUrl.startsWith('users/') 
                                        ? `https://assets.grok.com/${videoUrl}` 
                                        : videoUrl;

                                    console.log('📡 Grok Hook: Video URL Captured!', fullUrl);
                                    
                                    window.postMessage({
                                        source: 'grok-hook',
                                        action: 'VIDEO_CAPTURED',
                                        url: fullUrl,
                                        postId: streamResponse.videoPostId
                                    }, '*');
                                }
                            } catch (e) {
                                // 파싱 실패는 무시 (불완전한 JSON 라인 등)
                            }
                        }
                    }
                    if (!done) processStream();
                }).catch(err => console.error('❌ Grok Hook Stream Error:', err));
            }

            processStream();
            return response;
        });
    };
})();
