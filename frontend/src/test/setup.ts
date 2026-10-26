import "@testing-library/jest-dom";

// Mock para AudioContext en entorno Node/JSDOM
class MockAudioContext {
  state = "running";
  currentTime = 0;
  sampleRate = 44100;
  destination = {};

  createBuffer(channels: number, length: number, sampleRate: number) {
    return {
      numberOfChannels: channels,
      length,
      sampleRate,
      getChannelData: () => new Float32Array(length),
    };
  }

  createBufferSource() {
    return {
      buffer: null,
      connect: () => {},
      disconnect: () => {},
      start: () => {},
      stop: () => {},
      onended: null,
    };
  }

  resume() {
    return Promise.resolve();
  }

  decodeAudioData() {
    return Promise.resolve(this.createBuffer(1, 44100, 44100));
  }
}

// @ts-expect-error Mock global
window.AudioContext = MockAudioContext;
// @ts-expect-error Mock global
window.webkitAudioContext = MockAudioContext;
