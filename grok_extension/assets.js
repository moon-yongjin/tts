/**
 * Grok Bulk Assets Module
 * Manages storage and retrieval of image assets for @[Ref] fixation.
 */
class GrokAssets {
  static async getAsset(name) {
    const data = await chrome.storage.local.get(['grok_assets']);
    const assets = data.grok_assets || {};
    return assets[name];
  }

  static async saveAsset(name, dataUrl) {
    const data = await chrome.storage.local.get(['grok_assets']);
    const assets = data.grok_assets || {};
    assets[name] = dataUrl;
    await chrome.storage.local.set({ grok_assets: assets });
    console.log(`📦 Asset saved: ${name}`);
  }

  static async listAssets() {
    const data = await chrome.storage.local.get(['grok_assets']);
    return Object.keys(data.grok_assets || {});
  }

  static async deleteAsset(name) {
    const data = await chrome.storage.local.get(['grok_assets']);
    const assets = data.grok_assets || {};
    delete assets[name];
    await chrome.storage.local.set({ grok_assets: assets });
  }

  /**
   * DataURL을 Blob/File로 변환하여 업로드 준비
   */
  static dataURLtoFile(dataurl, filename) {
    var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
        bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
    while(n--){
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, {type:mime});
  }
}

// Window 전역 객체에 노출 (Content Script에서 사용)
window.GrokAssets = GrokAssets;
