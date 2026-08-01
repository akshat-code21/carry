export function eventLabel(type: string): string {
  switch (type) {
    case "video_detected":
      return "Video Detected";
    case "video_processed":
      return "Video Processed";
    case "video_failed":
      return "Processing Failed";
    default:
      return type.replaceAll("_", " ");
  }
}

export function eventBadgeClass(type: string): string {
  switch (type) {
    case "video_detected":
      return "bg-info/15 text-info";
    case "video_processed":
      return "bg-bullish/15 text-bullish";
    case "video_failed":
      return "bg-bearish/15 text-bearish";
    default:
      return "bg-panel-raised text-ink-secondary";
  }
}

export function timeAgo(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
