/* 医学监查后台进度 shell 前端。
 *
 * 合同：只消费 /progress 返回的受众白名单字段。页面不估算进度：
 * 全部数字与文字逐字段来自权威投影。未知字段一律忽略。
 */
(function () {
  "use strict";

  var POLL_MS = 1500;
  var STATE_TONES = { "未完成": "failed", "暂时受阻": "blocked" };

  var headline = document.getElementById("overall-headline");
  var bar = document.getElementById("overall-bar");
  var barFill = document.getElementById("overall-bar-fill");
  var counter = document.getElementById("overall-counter");
  var chips = document.getElementById("status-chips");
  var stageList = document.getElementById("stage-list");
  var currentPanel = document.getElementById("current-panel");
  var currentList = document.getElementById("current-list");
  var updateList = document.getElementById("update-list");
  var offlineNote = document.getElementById("offline-note");

  function setText(el, text) {
    el.textContent = text;
  }

  function clear(el) {
    while (el.firstChild) {
      el.removeChild(el.firstChild);
    }
  }

  function asNumber(value) {
    return typeof value === "number" && isFinite(value) && value >= 0
      ? value
      : 0;
  }

  function asText(value) {
    return typeof value === "string" ? value : "";
  }

  function renderOverall(view) {
    setText(headline, asText(view.headline) || "正在读取最新进度…");
    var percent = asNumber(view.percent);
    if (percent > 100) {
      percent = 100;
    }
    barFill.style.width = percent + "%";
    bar.setAttribute("aria-valuenow", String(percent));
    setText(counter, asText(view.progress_text) || "已处理 0/0 项");
  }

  function renderChips(view) {
    clear(chips);
    var overview = Array.isArray(view.status_overview) ? view.status_overview : [];
    overview.forEach(function (item) {
      if (!item || typeof item !== "object") {
        return;
      }
      var li = document.createElement("li");
      var label = asText(item.state_label);
      li.textContent = label + " " + asNumber(item.count) + " 项";
      if (STATE_TONES[label]) {
        li.setAttribute("data-tone", STATE_TONES[label]);
      }
      chips.appendChild(li);
    });
  }

  function renderStages(view) {
    clear(stageList);
    var stages = Array.isArray(view.stage_progress) ? view.stage_progress : [];
    if (!stages.length) {
      var empty = document.createElement("li");
      empty.className = "empty";
      empty.textContent = "暂无阶段进度。";
      stageList.appendChild(empty);
      return;
    }
    stages.forEach(function (stage) {
      if (!stage || typeof stage !== "object") {
        return;
      }
      var total = asNumber(stage.total);
      var processed = Math.min(asNumber(stage.processed), total || 0);
      var li = document.createElement("li");

      var name = document.createElement("span");
      name.className = "stages__name";
      name.textContent = asText(stage.stage);

      var barWrap = document.createElement("span");
      barWrap.className = "stages__bar";
      var fill = document.createElement("span");
      fill.className = "stages__bar-fill";
      fill.style.width = total > 0 ? (processed * 100) / total + "%" : "0%";
      barWrap.appendChild(fill);

      var text = document.createElement("span");
      text.className = "stages__text";
      setText(text, asText(stage.progress_text) || "已处理 0/0 项");

      li.appendChild(name);
      li.appendChild(barWrap);
      li.appendChild(text);
      stageList.appendChild(li);
    });
  }

  function renderCurrent(view) {
    clear(currentList);
    var items = Array.isArray(view.current_work) ? view.current_work : [];
    if (!items.length) {
      var empty = document.createElement("li");
      empty.className = "empty";
      empty.textContent = "当前没有正在处理的工作。";
      currentList.appendChild(empty);
      return;
    }
    items.forEach(function (work) {
      if (!work || typeof work !== "object") {
        return;
      }
      var li = document.createElement("li");
      var label = document.createElement("span");
      label.className = "current__label";
      label.textContent = asText(work.label);
      var meta = document.createElement("span");
      meta.className = "current__meta";
      var scope = asText(work.scope_label);
      var target = asText(work.target);
      var elapsed = asText(work.elapsed_text);
      var parts = [];
      if (scope && target) {
        parts.push(scope + "：" + target);
      }
      if (elapsed) {
        parts.push(elapsed);
      }
      meta.textContent = parts.join(" · ");
      li.appendChild(label);
      if (meta.textContent) {
        li.appendChild(meta);
      }
      currentList.appendChild(li);
    });
  }

  function renderUpdates(view) {
    clear(updateList);
    var items = Array.isArray(view.latest_updates) ? view.latest_updates : [];
    if (!items.length) {
      var empty = document.createElement("li");
      empty.className = "empty";
      empty.textContent = "暂无动态。";
      updateList.appendChild(empty);
      return;
    }
    items.forEach(function (update) {
      if (!update || typeof update !== "object") {
        return;
      }
      var li = document.createElement("li");
      var tone = STATE_TONES[asText(update.state_label)];
      if (tone) {
        li.setAttribute("data-tone", tone);
      }
      var time = document.createElement("span");
      time.className = "updates__time";
      time.textContent = asText(update.time_text);
      var message = document.createElement("span");
      message.className = "updates__message";
      message.textContent = asText(update.message);
      li.appendChild(time);
      li.appendChild(message);
      updateList.appendChild(li);
    });
  }

  function renderView(view) {
    offlineNote.hidden = true;
    renderOverall(view);
    renderChips(view);
    renderStages(view);
    renderCurrent(view);
    renderUpdates(view);
    document.body.setAttribute("data-shell-state", "ready");
  }

  function markOffline() {
    offlineNote.hidden = false;
    document.body.setAttribute("data-shell-state", "offline");
  }

  function tick() {
    fetch("/progress", { headers: { Accept: "application/json" } })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("progress unavailable");
        }
        return response.json();
      })
      .then(renderView)
      .catch(markOffline);
  }

  tick();
  window.setInterval(tick, POLL_MS);
})();
