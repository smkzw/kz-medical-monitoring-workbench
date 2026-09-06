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
    const version = ++requestVersion.current;
    try {
      const result = await api.setQueuePaused(projectId, !queue.pause_requested);
      if (alive.current && version === requestVersion.current) {
        setQueue(result);
        setError("");
      }
    } catch {
      if (alive.current) setError("操作未能确认，请稍后重试；已整理的内容会保留。");
    } finally {
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
