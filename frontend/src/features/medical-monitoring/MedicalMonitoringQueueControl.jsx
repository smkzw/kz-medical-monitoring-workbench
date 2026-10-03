import { useEffect, useRef, useState } from "react";

export default function MedicalMonitoringQueueControl({ api, projectId }) {
  const [queue, setQueue] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const requestVersion = useRef(0);
  const changing = useRef(false);
  const alive = useRef(false);

  useEffect(() => {
    alive.current = true;
    const controller = new AbortController();
    let timer;
    async function refresh() {
      if (!changing.current) {
        const version = ++requestVersion.current;
        try {
          const result = await api.getQueueState(projectId, { signal: controller.signal });
          if (alive.current && version === requestVersion.current) {
            setQueue(result);
            setError("");
          }
        } catch (failure) {
          if (alive.current && version === requestVersion.current && failure.name !== "AbortError") {
            setError("暂时无法读取整理状态，请稍后重试。");
          }
        }
      }
      if (alive.current) timer = setTimeout(refresh, 5000);
    }
    refresh();
    return () => {
      alive.current = false;
      requestVersion.current += 1;
      controller.abort();
      clearTimeout(timer);
    };
  }, [api, projectId]);

  async function change() {
    if (!queue || changing.current) return;
    changing.current = true;
    setBusy(true);
    const nextPaused = !queue.pause_requested;
    // R12轮（R10-01）：乐观UI——点击立即翻转文案（≤1秒可见变化），
    // 请求带8秒超时（实测后端曾挂起5分钟），失败回滚并明示。
    setQueue((current) => current ? { ...current, pause_requested: nextPaused } : current);
    const version = ++requestVersion.current;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const result = await api.setQueuePaused(projectId, nextPaused, { signal: controller.signal });
      if (alive.current && version === requestVersion.current) {
        setQueue(result);
        setError("");
      }
    } catch {
      if (alive.current) {
        setQueue((current) => current ? { ...current, pause_requested: !nextPaused } : current);
        setError(nextPaused
          ? "暂停请求未在8秒内确认，已还原状态；请稍后重试（已整理的内容会保留）。"
          : "继续整理请求未在8秒内确认，已还原状态；请稍后重试。");
      }
    } finally {
      clearTimeout(timeout);
      changing.current = false;
      if (alive.current) setBusy(false);
    }
  }

  return (
    <section className="monitoring-admission-queue-control" aria-label="资料整理控制">
      <p role="status">{queue?.state === "pausing" ? "正在保存当前结果，保存后暂停。"
        : queue?.pause_requested ? "资料整理已暂停，已完成的内容会保留。"
          : "整理在后台进行时，可以离开页面，稍后再查看。"}</p>
      {error ? <p role="alert">{error}</p> : null}
      <button type="button" className="monitoring-admission-secondary" disabled={!queue || busy} onClick={change}>
        {busy ? "正在处理…" : queue?.pause_requested ? "继续整理" : "暂停整理"}
      </button>
    </section>
  );
}
