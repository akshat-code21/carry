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
      return "bg-success/15 text-success";
    case "video_failed":
      return "bg-danger/15 text-danger";
    default:
      return "bg-muted text-muted-foreground";
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
