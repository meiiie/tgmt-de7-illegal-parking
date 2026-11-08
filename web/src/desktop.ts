type DesktopWindow = Window & { chrome?: { webview?: { postMessage: (message: string) => void } } };

export const isDesktop = () => Boolean((window as DesktopWindow).chrome?.webview);
export function desktopAction(action: "open-data" | "restore-backup") {
  (window as DesktopWindow).chrome?.webview?.postMessage(action);
}
